"""
Shodan fetcher — queries Shodan host intelligence for an IP address.
Returns a RawDocument with open ports, services, vulns in metadata.
Requires SHODAN_API_KEY in config.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Optional

import httpx
import structlog

from tracr.config import settings
from tracr.ingestion.normalizer import RawDocument

logger = structlog.get_logger()

SHODAN_HOST_URL = "https://api.shodan.io/shodan/host/{ip}?key={key}"
SHODAN_DNS_URL = "https://api.shodan.io/dns/resolve?hostnames={domain}&key={key}"


async def _resolve_domain_to_ip(domain: str) -> Optional[str]:
    """Resolve a domain to IP via Shodan DNS API."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            url = SHODAN_DNS_URL.format(domain=domain, key=settings.SHODAN_API_KEY)
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get(domain)
    except Exception as e:
        logger.warning("shodan.dns_resolve_failed", domain=domain, error=str(e))
        return None


async def fetch_shodan(source_id: str, url: str) -> list[RawDocument]:
    """
    Query Shodan for host intelligence on an IP or domain.
    url is the IP or domain to look up.
    Returns a single RawDocument with Shodan data in metadata.
    """
    log = logger.bind(source_id=source_id, target=url)

    if not settings.SHODAN_API_KEY:
        log.warning("shodan.no_api_key")
        return []

    # Resolve domain to IP if needed
    target = url
    if not _is_ip(url):
        target = await _resolve_domain_to_ip(url)
        if not target:
            log.warning("shodan.dns_resolution_failed", domain=url)
            return []

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                SHODAN_HOST_URL.format(ip=target, key=settings.SHODAN_API_KEY)
            )
            if response.status_code == 404:
                log.warning("shodan.host_not_found", ip=target)
                return []
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        log.warning("shodan.request_failed", error=str(e))
        return []

    fetched_at = datetime.now(timezone.utc)

    # Extract key intelligence
    ports = sorted(set(data.get("ports", [])))
    hostnames = data.get("hostnames", [])
    vulns = list(data.get("vulns", {}).keys())
    org = data.get("org", "")
    country = data.get("country_name", "")
    isp = data.get("isp", "")
    os_info = data.get("os", "")

    # Extract service banners
    services = []
    for item in data.get("data", []):
        svc = {
            "port": item.get("port"),
            "transport": item.get("transport"),
            "product": item.get("product"),
            "version": item.get("version"),
            "cpe": item.get("cpe"),
        }
        services.append(svc)

    metadata = {
        "ip": target,
        "original_target": url,
        "ports": ports,
        "hostnames": hostnames,
        "org": org,
        "country": country,
        "isp": isp,
        "os": os_info,
        "vulns": vulns,
        "services": services,
        "last_update": data.get("last_update"),
    }

    # Build text summary for NLP
    body_parts = [f"Shodan intelligence for {target}"]
    if org:
        body_parts.append(f"Organisation: {org}")
    if country:
        body_parts.append(f"Country: {country}")
    if isp:
        body_parts.append(f"ISP: {isp}")
    if ports:
        body_parts.append(f"Open ports: {', '.join(str(p) for p in ports)}")
    if hostnames:
        body_parts.append(f"Hostnames: {', '.join(hostnames)}")
    if vulns:
        body_parts.append(f"Vulnerabilities: {', '.join(vulns)}")
    if os_info:
        body_parts.append(f"Operating system: {os_info}")
    body = "\n".join(body_parts)

    doc_url = f"shodan://{target}"
    url_hash = hashlib.sha256(doc_url.encode()).hexdigest()
    content_hash = hashlib.sha256(body.encode()).hexdigest()

    doc = RawDocument(
        source_id=source_id,
        url=doc_url,
        title=f"Shodan: {target}",
        body=body,
        published_at=fetched_at,
        fetched_at=fetched_at,
        url_hash=url_hash,
        content_hash=content_hash,
        metadata=metadata,
    )

    log.info("shodan.complete", ip=target, ports=len(ports), vulns=len(vulns))
    return [doc]


def _is_ip(value: str) -> bool:
    """Check if a string looks like an IPv4 address."""
    import re
    return bool(re.match(
        r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", value
    ))
