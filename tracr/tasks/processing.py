import asyncio

import structlog

from tracr.processing.processor import process_document
from tracr.tasks.ingestion import celery_app

logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_doc(self, document_id: str):
    """Run NLP processing on a single document."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(process_document(document_id))
    finally:
        loop.close()
