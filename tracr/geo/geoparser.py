"""
Mordecai3 geoparser client — resolves place mentions in text to coordinates.
Calls the mordecai3 REST service (backed by Elasticsearch + GeoNames).
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx
import structlog

from tracr.config import settings

logger = structlog.get_logger()


@dataclass
class GeoparsedPlace:
    place_name: str
    latitude: float
    longitude: float
    country_code: str
    geonames_id: int
    confidence: float
    source: str = "mordecai3"


async def geoparse_text(text: str) -> list[GeoparsedPlace]:
    """
    Send text to the mordecai3 service and return resolved place mentions.
    Returns empty list if service is unavailable.
    """
    if not text or not text.strip():
        return []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.MORDECAI_URL}/geoparse",
                json={"text": text},
            )
            response.raise_for_status()
            data = response.json()

        places = []
        for item in data:
            geo = item.get("geo", {})
            if not geo.get("lat") or not geo.get("lon"):
                continue
            places.append(GeoparsedPlace(
                place_name=item.get("word", ""),
                latitude=float(geo["lat"]),
                longitude=float(geo["lon"]),
                country_code=geo.get("country_code3", ""),
                geonames_id=int(geo.get("geonameid", 0)),
                confidence=float(item.get("score", 0.5)),
            ))

        logger.info("geoparser.complete", count=len(places))
        return places

    except httpx.ConnectError:
        logger.warning("geoparser.unavailable", url=settings.MORDECAI_URL)
        return []
    except Exception as e:
        logger.warning("geoparser.error", error=str(e))
        return []
