"""
Celery geo task: extract and store location events for a document.
Runs on the dedicated 'geo' queue.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tracr.config import settings
from tracr.db.models import LocationEvent, GeoSourceType, RawDocument, Mention, Entity
from tracr.tasks.ingestion import celery_app

logger = structlog.get_logger()


def _pg_session():
    engine = create_async_engine(
        settings.DATABASE_URL, pool_size=5, max_overflow=10, pool_pre_ping=True
    )
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False), engine


@celery_app.task(
    name="tracr.tasks.geo.geolocate_document",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="geo",
)
def geolocate_document(self, document_id: str):
    """
    Run full geolocation pipeline on a processed document:
    1. IP geolocation on any IPs found in document text
    2. Mordecai3 geoparsing on document text
    Results are stored as LocationEvent rows linked to the document
    and any entities mentioned in it.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_geolocate_async(document_id))
    finally:
        loop.close()


async def _geolocate_async(document_id: str) -> dict:
    from tracr.geo.ipgeo import geolocate_text
    from tracr.geo.geoparser import geoparse_text

    log = logger.bind(document_id=document_id)
    SessionLocal, engine = _pg_session()

    try:
        async with SessionLocal() as db:
            # Load document
            result = await db.execute(
                select(RawDocument).where(
                    RawDocument.id == uuid.UUID(document_id)
                )
            )
            doc = result.scalar_one_or_none()
            if not doc:
                log.warning("geo.document_not_found")
                return {"status": "skipped"}

            text = " ".join(filter(None, [doc.title, doc.body]))
            if not text.strip():
                return {"status": "skipped", "reason": "empty text"}

            # Load entity IDs mentioned in this document
            mentions_result = await db.execute(
                select(Mention.entity_id).where(
                    Mention.document_id == uuid.UUID(document_id)
                ).distinct()
            )
            entity_ids = [str(row[0]) for row in mentions_result.fetchall()]
            # Use first entity as primary link (most prominent)
            primary_entity_id = uuid.UUID(entity_ids[0]) if entity_ids else None

            saved = 0
            now = datetime.now(timezone.utc)

            # 1. IP geolocation
            ip_locations = await geolocate_text(text)
            for loc in ip_locations:
                event = LocationEvent(
                    entity_id=primary_entity_id,
                    document_id=uuid.UUID(document_id),
                    latitude=loc.latitude,
                    longitude=loc.longitude,
                    place_name=loc.city or None,
                    country_code=loc.country or None,
                    geo_source=GeoSourceType.ip_geo,
                    confidence=0.7,
                    raw_data={"ip": loc.ip, "isp": loc.isp},
                    observed_at=now,
                )
                db.add(event)
                saved += 1

            # 2. Mordecai3 text geoparsing
            geo_places = await geoparse_text(text)
            for place in geo_places:
                event = LocationEvent(
                    entity_id=primary_entity_id,
                    document_id=uuid.UUID(document_id),
                    latitude=place.latitude,
                    longitude=place.longitude,
                    place_name=place.place_name,
                    country_code=place.country_code or None,
                    geo_source=GeoSourceType.mordecai3,
                    confidence=place.confidence,
                    raw_data={"geonames_id": place.geonames_id},
                    observed_at=now,
                )
                db.add(event)
                saved += 1

            await db.commit()
            log.info("geo.complete", saved=saved)
            return {"status": "ok", "saved": saved}

    finally:
        await engine.dispose()
