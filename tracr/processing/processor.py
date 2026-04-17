import uuid
from datetime import datetime, timezone

import httpx
import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tracr.config import settings
from tracr.db.models import Entity, Mention, ProcessingStatus, RawDocument
from tracr.processing.ner import ExtractedMention
from tracr.processing.resolver import resolve_entities

logger = structlog.get_logger()

NLP_SERVICE_URL = "http://nlp-service:3000"


def get_session_factory():
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    ), engine


async def call_nlp_service(text: str) -> list[ExtractedMention]:
    """Call BentoML NLP service to extract named entities from text."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{NLP_SERVICE_URL}/extract",
            json={"request": {"text": text}},
        )
        response.raise_for_status()
        return [ExtractedMention(**m) for m in response.json()]


async def process_document(document_id: str):
    log = logger.bind(document_id=document_id)
    SessionLocal, engine = get_session_factory()

    try:
        async with SessionLocal() as db:
            result = await db.execute(
                select(RawDocument).where(
                    RawDocument.id == uuid.UUID(document_id)
                )
            )
            doc = result.scalar_one_or_none()
            if not doc:
                log.warning("processor.document_not_found")
                return {"status": "skipped"}

            await db.execute(
                update(RawDocument)
                .where(RawDocument.id == uuid.UUID(document_id))
                .values(processing_status=ProcessingStatus.processing)
            )
            await db.commit()

            text = " ".join(filter(None, [doc.title, doc.body]))
            if not text.strip():
                await db.execute(
                    update(RawDocument)
                    .where(RawDocument.id == uuid.UUID(document_id))
                    .values(processing_status=ProcessingStatus.done)
                )
                await db.commit()
                return {"status": "skipped", "reason": "empty text"}

            # Call BentoML NLP service
            mentions = await call_nlp_service(text)
            log.info("processor.ner_complete", mention_count=len(mentions))

            if not mentions:
                await db.execute(
                    update(RawDocument)
                    .where(RawDocument.id == uuid.UUID(document_id))
                    .values(processing_status=ProcessingStatus.done)
                )
                await db.commit()
                return {"status": "ok", "entities": 0, "mentions": 0}

            mention_pairs = [(m.text, m.entity_type) for m in mentions]
            resolved = resolve_entities(mention_pairs)
            log.info("processor.resolved", entity_count=len(resolved))

            now = datetime.now(timezone.utc)
            saved_entities = 0
            saved_mentions = 0

            for resolved_entity in resolved:
                result = await db.execute(
                    select(Entity).where(
                        Entity.canonical_name == resolved_entity.canonical_name,
                        Entity.entity_type == resolved_entity.entity_type,
                    )
                )
                entity = result.scalar_one_or_none()

                if not entity:
                    entity = Entity(
                        canonical_name=resolved_entity.canonical_name,
                        entity_type=resolved_entity.entity_type,
                        aliases=resolved_entity.aliases,
                        confidence=resolved_entity.confidence,
                        first_seen=now,
                        last_seen=now,
                        metadata_={},
                    )
                    db.add(entity)
                    await db.flush()
                    saved_entities += 1
                else:
                    existing_aliases = set(entity.aliases or [])
                    new_aliases = existing_aliases | set(resolved_entity.aliases)
                    entity.aliases = list(new_aliases)
                    entity.last_seen = now
                    entity.confidence = min(1.0, entity.confidence + 0.05)

                for raw_mention in mentions:
                    if raw_mention.text in resolved_entity.aliases:
                        mention = Mention(
                            entity_id=entity.id,
                            document_id=doc.id,
                            snippet=raw_mention.snippet,
                            char_start=raw_mention.char_start,
                            char_end=raw_mention.char_end,
                            score=raw_mention.score,
                        )
                        db.add(mention)
                        saved_mentions += 1

            await db.execute(
                update(RawDocument)
                .where(RawDocument.id == uuid.UUID(document_id))
                .values(processing_status=ProcessingStatus.done)
            )

            await db.commit()
            log.info("processor.complete",
                      entities=saved_entities, mentions=saved_mentions)
            return {
                "status": "ok",
                "entities": saved_entities,
                "mentions": saved_mentions,
            }

    except Exception as e:
        log.error("processor.failed", error=str(e))
        async with SessionLocal() as db:
            await db.execute(
                update(RawDocument)
                .where(RawDocument.id == uuid.UUID(document_id))
                .values(processing_status=ProcessingStatus.failed)
            )
            await db.commit()
        raise
    finally:
        await engine.dispose()
