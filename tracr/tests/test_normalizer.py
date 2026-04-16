from datetime import datetime, timezone
from tracr.ingestion.normalizer import RawDocument


def test_from_feed_entry_basic():
    entry = {
        "link": "https://example.com/article-1",
        "title": "Test Article",
        "summary": "This is a test article about Africa.",
    }
    doc = RawDocument.from_feed_entry(
        entry=entry,
        source_id="test-source-id",
        fetched_at=datetime.now(timezone.utc),
    )
    assert doc.url == "https://example.com/article-1"
    assert doc.title == "Test Article"
    assert doc.body == "This is a test article about Africa."
    assert doc.url_hash is not None
    assert len(doc.url_hash) == 64


def test_url_hash_is_deterministic():
    entry = {"link": "https://example.com/article-1", "title": "Test"}
    doc1 = RawDocument.from_feed_entry(
        entry=entry,
        source_id="source-1",
        fetched_at=datetime.now(timezone.utc),
    )
    doc2 = RawDocument.from_feed_entry(
        entry=entry,
        source_id="source-1",
        fetched_at=datetime.now(timezone.utc),
    )
    assert doc1.url_hash == doc2.url_hash


def test_content_hash_generated():
    entry = {
        "link": "https://example.com/article-2",
        "title": "Another Article",
        "summary": "Content here.",
    }
    doc = RawDocument.from_feed_entry(
        entry=entry,
        source_id="source-1",
        fetched_at=datetime.now(timezone.utc),
    )
    assert doc.content_hash is not None


def test_missing_url_handled():
    entry = {"title": "No URL Article", "summary": "Content."}
    doc = RawDocument.from_feed_entry(
        entry=entry,
        source_id="source-1",
        fetched_at=datetime.now(timezone.utc),
    )
    assert doc.url == ""
