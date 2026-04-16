"""
Celery Beat periodic task: fan out ingestion jobs for all active sources.
"""
import asyncio

import structlog
from sqlalchemy import select

from tracr.db.models import Source
from tracr.tasks.ingestion import celery_app, get_session_factory

logger = structlog.get_logger()


@celery_app.task(name="tracr.tasks.scheduler.ingest_all_sources")
def ingest_all_sources():
    """
    Periodic entry point (fires every 15 minutes via Celery Beat).
    Fetches all active sources from the DB and enqueues an ingest_source
    task for each one onto the ingestion queue.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        source_ids = loop.run_until_complete(_fetch_active_source_ids())
    finally:
        loop.close()

    from tracr.tasks.ingestion import ingest_source

    for sid in source_ids:
        ingest_source.apply_async(args=[sid], queue="ingestion")

    logger.info("scheduler.ingest_all_sources.dispatched", count=len(source_ids))
    return {"dispatched": len(source_ids)}


async def _fetch_active_source_ids() -> list[str]:
    SessionLocal, engine = get_session_factory()
    try:
        async with SessionLocal() as db:
            result = await db.execute(
                select(Source.id).where(Source.active.is_(True))
            )
            return [str(row[0]) for row in result.fetchall()]
    finally:
        await engine.dispose()
