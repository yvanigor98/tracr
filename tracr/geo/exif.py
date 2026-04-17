"""
EXIF GPS extractor — pulls lat/lon from image metadata.
Supports JPEG, TIFF, and any Pillow-readable format with GPS EXIF tags.
"""
from __future__ import annotations

import io
import struct
from dataclasses import dataclass
from typing import Optional

import structlog
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

logger = structlog.get_logger()


@dataclass
class GPSCoordinate:
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    source: str = "exif"


def _convert_dms_to_decimal(dms: tuple, ref: str) -> float:
    """Convert degrees/minutes/seconds tuple to decimal degrees."""
    degrees = float(dms[0])
    minutes = float(dms[1])
    seconds = float(dms[2])
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if ref in ("S", "W"):
        decimal = -decimal
    return decimal


def extract_gps_from_bytes(image_bytes: bytes) -> Optional[GPSCoordinate]:
    """
    Extract GPS coordinates from raw image bytes.
    Returns None if no GPS data is present.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        exif_data = image._getexif()
        if not exif_data:
            return None

        gps_info: dict = {}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == "GPSInfo":
                for gps_tag_id, gps_value in value.items():
                    gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_info[gps_tag] = gps_value

        if not gps_info:
            return None

        lat = _convert_dms_to_decimal(
            gps_info["GPSLatitude"], gps_info["GPSLatitudeRef"]
        )
        lon = _convert_dms_to_decimal(
            gps_info["GPSLongitude"], gps_info["GPSLongitudeRef"]
        )
        alt = None
        if "GPSAltitude" in gps_info:
            alt = float(gps_info["GPSAltitude"])
            if gps_info.get("GPSAltitudeRef") == b"\x01":
                alt = -alt

        logger.info("exif.gps_extracted", lat=lat, lon=lon)
        return GPSCoordinate(latitude=lat, longitude=lon, altitude=alt)

    except Exception as e:
        logger.warning("exif.extraction_failed", error=str(e))
        return None


def extract_gps_from_path(path: str) -> Optional[GPSCoordinate]:
    """Extract GPS coordinates from an image file path."""
    with open(path, "rb") as f:
        return extract_gps_from_bytes(f.read())
