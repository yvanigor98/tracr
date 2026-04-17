"""
WHOIS fetcher — performs WHOIS lookup for a domain or IP address.
Returns a RawDocument with structured WHOIS data in metadata.
"""
from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, timezone

import structlog
import whois

from tracr.ingestion.normalizer import RawDocument

logger = structlog.get_logger()


async def fetch_whois(source_id: str, url: str) -> list[RawDocument]:
    """
    Perform a WHOIS lookup on a domain or IP.
    url is the domain/IP to look up (e.g. "example.com" or "8.8.8.8").
    Returns a single RawDocument with WHOIS data in metadata.
    """
    log = logger.bind(source_id=source_id, target=url)

    try:
        # whois is synchronous — run in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, whois.whois, url)
    except Exception as e:
        log.warning("whois.lookup_failed", error=str(e))
        return []

    if not result or not result.domain_name:
        log.warning("whois.no_data", target=url)
        return []

    fetched_at = datetime.now(timezone.utc)

    # Normalise domain name
    domain = result.domain_name
    if isinstance(domain, list):
        domain = domain[0]
    domain = domain.lower()

    # Build structured metadata
    def _serialise(v):
        if isinstance(v, list):
            return [str(i) for i in v]
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v) if v else None

    metadata = {
        "domain": domain,
        "registrar": _serialise(result.registrar),
        "creation_date": _serialise(result.creation_date),
        "expiration_date": _serialise(result.expiration_date),
        "updated_date": _serialise(result.updated_date),
        "name_servers": _serialise(result.name_servers),
        "status": _serialise(result.status),
        "emails": _serialise(result.emails),
        "org": _serialise(result.org),
        "country": _serialise(result.country),
        "registrant_name": _serialise(result.name),
    }

    # Build a text summary for NLP processing
    body_parts = [f"WHOIS record for {domain}"]
    if result.registrar:
        body_parts.append(f"Registrar: {result.registrar}")
    if result.org:
        body_parts.append(f"Organisation: {result.org}")
    if result.country:
        body_parts.append(f"Country: {result.country}")
    if result.emails:
        emails = result.emails if isinstance(result.emails, list) else [result.emails]
        body_parts.append(f"Emails: {', '.join(str(e) for e in emails)}")
    body = "\n".join(body_parts)

    doc_url = f"whois://{domain}"
    url_hash = hashlib.sha256(doc_url.encode()).hexdigest()
    content_hash = hashlib.sha256(body.encode()).hexdigest()

    doc = RawDocument(
        source_id=source_id,
        url=doc_url,
        title=f"WHOIS: {domain}",
        body=body,
        published_at=fetched_at,
        fetched_at=fetched_at,
        url_hash=url_hash,
        content_hash=content_hash,
        metadata=metadata,
    )

    log.info("whois.complete", domain=domain)
    return [doc]
