import hashlib
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawDocument:
    source_id: str
    url: str
    title: str | None
    body: str | None
    published_at: datetime | None
    fetched_at: datetime
    url_hash: str
    content_hash: str | None
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_feed_entry(cls, entry: dict, source_id: str, fetched_at: datetime) -> "RawDocument":
        url = entry.get("link") or entry.get("id") or ""
        title = entry.get("title")
        body = entry.get("summary") or entry.get("content", [{}])[0].get("value")

        published_at = None
        if entry.get("published_parsed"):
            import calendar
            published_at = datetime.utcfromtimestamp(
                calendar.timegm(entry["published_parsed"])
            )

        url_hash = hashlib.sha256(url.encode()).hexdigest()
        content_hash = (
            hashlib.sha256((title or "" + body or "").encode()).hexdigest()
            if (title or body)
            else None
        )

        return cls(
            source_id=source_id,
            url=url,
            title=title,
            body=body,
            published_at=published_at,
            fetched_at=fetched_at,
            url_hash=url_hash,
            content_hash=content_hash,
            metadata={
                "tags": [t.get("term") for t in entry.get("tags", [])],
                "author": entry.get("author"),
            },
        )
