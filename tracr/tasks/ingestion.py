import asyncio
import uuid
from datetime import datetime, timezone

import structlog
from celery import Celery
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from tracr.config import settings
from tracr.db.models import ProcessingStatus, RawDocument as RawDocumentModel, Source
from tracr.ingestion.fetchers.rss import fetch_feed

logger = structlog.get_logger()

celery_app = Celery(
    "tracr",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "tracr.tasks.ingestion.*": {"queue": "ingestion"},
        "tracr.tasks.processing.*": {"queue": "processing"},
        "tracr.tasks.geo.*": {"queue": "geo"},
    },
)


def get_session_factory():
    """Create a fresh engine and session factory for each task execution."""
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


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def ingest_source(self, source_id: str):
    """Fetch and store documents from a single source."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_ingest_source_async(source_id))
    finally:
        loop.close()


async def _ingest_source_async(source_id: str):
    log = logger.bind(source_id=source_id)
    SessionLocal, engine = get_session_factory()

    try:
        async with SessionLocal() as db:
            result = await db.execute(
                select(Source).where(Source.id == uuid.UUID(source_id))
            )
            source = result.scalar_one_or_none()

            if not source or not source.active:
                log.warning("ingestion.source_not_found_or_inactive")
                return {"status": "skipped", "reason": "not found or inactive"}

            log.info("ingestion.start", url=source.url, type=source.type)

            if source.type == "rss":
                documents = await fetch_feed(source_id=source_id, url=source.url)
            else:
                log.warning("ingestion.unsupported_type", type=source.type)
                return {"status": "skipped", "reason": f"unsupported type: {source.type}"}

            saved = 0
            for doc in documents:
                db_doc = RawDocumentModel(
                    source_id=uuid.UUID(source_id),
                    url=doc.url,
                    url_hash=doc.url_hash,
                    content_hash=doc.content_hash,
                    title=doc.title,
                    body=doc.body,
                    published_at=doc.published_at,
                    fetched_at=doc.fetched_at,
                    processing_status=ProcessingStatus.pending,
                    metadata_=doc.metadata,
                )
                db.add(db_doc)
                saved += 1

            await db.execute(
                update(Source)
                .where(Source.id == uuid.UUID(source_id))
                .values(last_fetched_at=datetime.now(timezone.utc))
            )

            await db.commit()
            log.info("ingestion.complete", saved=saved)
            return {"status": "ok", "saved": saved}
    finally:
        await engine.dispose()


@celery_app.task
def process_pending_documents():
    """Queue NLP processing for all pending documents."""
    import asyncio
    from sqlalchemy import select
    from tracr.db.models import ProcessingStatus, RawDocument as RawDocumentModel

    async def _get_pending():
        SessionLocal, engine = get_session_factory()
        try:
            async with SessionLocal() as db:
                result = await db.execute(
                    select(RawDocumentModel.id).where(
                        RawDocumentModel.processing_status == ProcessingStatus.pending
                    ).limit(100)
                )
                return [str(row[0]) for row in result.fetchall()]
        finally:
            await engine.dispose()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        pending_ids = loop.run_until_complete(_get_pending())
    finally:
        loop.close()

    from tracr.tasks.processing import process_doc
    for doc_id in pending_ids:
        process_doc.apply_async(args=[doc_id], queue="processing")

    logger.info("ingestion.queued_processing", count=len(pending_ids))
    return {"queued": len(pending_ids)}


# ---------------------------------------------------------------------------
# Beat schedule — periodic tasks
# ---------------------------------------------------------------------------
celery_app.conf.beat_schedule = {
    "ingest-all-sources-every-15-minutes": {
        "task": "tracr.tasks.scheduler.ingest_all_sources",
        "schedule": 900.0,  # seconds — 15 minutes
    },
    "process-pending-documents-every-5-minutes": {
        "task": "tracr.tasks.ingestion.process_pending_documents",
        "schedule": 300.0,  # seconds — 5 minutes
    },
}

# Graph sync — added Phase 2 Step 3
celery_app.conf.beat_schedule["sync-graph-every-30-minutes"] = {
    "task": "tracr.tasks.graph.sync_graph",
    "schedule": 1800.0,
}
