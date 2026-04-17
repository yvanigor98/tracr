"""
Celery task: sync Postgres entity data to Neo4j graph.
"""
import asyncio

import structlog

from tracr.tasks.ingestion import celery_app

logger = structlog.get_logger()


@celery_app.task(name="tracr.tasks.graph.sync_graph", bind=True, max_retries=3)
def sync_graph(self):
    """Sync all entities and co-occurrence relationships to Neo4j."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_sync())
    finally:
        loop.close()


async def _sync():
    from tracr.graph.driver import get_driver
    from tracr.graph.schema import init_schema
    from tracr.graph.sync import sync_entities

    driver = await get_driver()
    await init_schema(driver)
    result = await sync_entities(driver)
    return result
