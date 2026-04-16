import asyncio
from datetime import datetime, timezone

import feedparser
import httpx
import structlog

from tracr.ingestion.dedup import bloom
from tracr.ingestion.normalizer import RawDocument

logger = structlog.get_logger()

HEADERS = {
    "User-Agent": "Tracr/0.1 OSINT Platform (https://github.com/yvanigor98/tracr)",
}

MAX_RETRIES = 3
RETRY_BACKOFF = 2.0


async def fetch_feed(source_id: str, url: str) -> list[RawDocument]:
    """
    Fetch and parse an RSS/Atom feed.
    Returns a list of new (non-duplicate) RawDocuments.
    """
    log = logger.bind(source_id=source_id, url=url)

    raw_content = await _fetch_with_retry(url, log)
    if not raw_content:
        return []

    feed = feedparser.parse(raw_content)

    if feed.bozo and not feed.entries:
        log.warning("rss.parse_error", error=str(feed.bozo_exception))
        return []

    log.info("rss.fetched", entry_count=len(feed.entries))

    fetched_at = datetime.now(timezone.utc)
    documents = []

    for entry in feed.entries:
        doc = RawDocument.from_feed_entry(
            entry=dict(entry),
            source_id=source_id,
            fetched_at=fetched_at,
        )

        if not doc.url:
            continue

        # Dedup check
        if await bloom.exists(doc.url_hash):
            log.debug("rss.dedup_skip", url=doc.url)
            continue

        await bloom.add(doc.url_hash)
        documents.append(doc)

    log.info("rss.new_documents", count=len(documents))
    return documents


async def _fetch_with_retry(url: str, log) -> bytes | None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(
                headers=HEADERS,
                timeout=30.0,
                follow_redirects=True,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
        except httpx.HTTPStatusError as e:
            log.warning("rss.http_error", status=e.response.status_code, attempt=attempt)
        except httpx.RequestError as e:
            log.warning("rss.request_error", error=str(e), attempt=attempt)

        if attempt < MAX_RETRIES:
            await asyncio.sleep(RETRY_BACKOFF ** attempt)

    log.error("rss.fetch_failed", max_retries=MAX_RETRIES)
    return None
