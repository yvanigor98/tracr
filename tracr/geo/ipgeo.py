"""
IP geolocation — resolves IP addresses found in text to lat/lon.
Uses ip-api.com (free tier, no API key, 45 req/min).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import httpx
import structlog

logger = structlog.get_logger()

IP_PATTERN = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)

IP_API_URL = "http://ip-api.com/json/{ip}?fields=status,lat,lon,country,city,isp"

# Private/reserved IP ranges to skip
SKIP_PREFIXES = ("10.", "192.168.", "127.", "0.", "172.16.", "172.17.",
                 "172.18.", "172.19.", "172.2", "172.3")


@dataclass
class IPLocation:
    ip: str
    latitude: float
    longitude: float
    country: str
    city: str
    isp: str
    source: str = "ip_geo"


def extract_ips(text: str) -> list[str]:
    """Extract all public IP addresses from text."""
    ips = IP_PATTERN.findall(text)
    return [ip for ip in ips if not any(ip.startswith(p) for p in SKIP_PREFIXES)]


async def geolocate_ip(ip: str) -> Optional[IPLocation]:
    """Resolve a single IP address to coordinates via ip-api.com."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(IP_API_URL.format(ip=ip))
            response.raise_for_status()
            data = response.json()

        if data.get("status") != "success":
            logger.warning("ipgeo.failed", ip=ip, status=data.get("status"))
            return None

        return IPLocation(
            ip=ip,
            latitude=data["lat"],
            longitude=data["lon"],
            country=data.get("country", ""),
            city=data.get("city", ""),
            isp=data.get("isp", ""),
        )
    except Exception as e:
        logger.warning("ipgeo.error", ip=ip, error=str(e))
        return None


async def geolocate_text(text: str) -> list[IPLocation]:
    """Extract and geolocate all public IPs found in text."""
    ips = extract_ips(text)
    results = []
    for ip in ips:
        location = await geolocate_ip(ip)
        if location:
            results.append(location)
    return results
