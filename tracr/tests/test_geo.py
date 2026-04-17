"""Tests for geolocation layer."""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest


def test_extract_ips_finds_public_ips():
    from tracr.geo.ipgeo import extract_ips
    text = "Server at 8.8.8.8 and internal 192.168.1.1 and 41.86.99.1"
    ips = extract_ips(text)
    assert "8.8.8.8" in ips
    assert "41.86.99.1" in ips
    assert "192.168.1.1" not in ips


def test_extract_ips_empty_text():
    from tracr.geo.ipgeo import extract_ips
    assert extract_ips("No IP addresses here.") == []


def test_extract_gps_returns_none_for_non_image():
    from tracr.geo.exif import extract_gps_from_bytes
    assert extract_gps_from_bytes(b"not an image") is None


def test_extract_gps_returns_none_for_image_without_gps():
    from tracr.geo.exif import extract_gps_from_bytes
    from PIL import Image
    import io
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    assert extract_gps_from_bytes(buf.getvalue()) is None


@pytest.mark.asyncio
async def test_geolocate_ip_parses_response():
    from tracr.geo.ipgeo import geolocate_ip
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "status": "success", "lat": -1.286389, "lon": 36.817223,
        "country": "Kenya", "city": "Nairobi", "isp": "Safaricom",
    }
    mock_response.raise_for_status = MagicMock()
    with patch("tracr.geo.ipgeo.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(get=AsyncMock(return_value=mock_response))
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        result = await geolocate_ip("41.86.99.1")
    assert result is not None
    assert result.latitude == -1.286389
    assert result.city == "Nairobi"
    assert result.source == "ip_geo"


@pytest.mark.asyncio
async def test_geolocate_ip_returns_none_on_failure():
    from tracr.geo.ipgeo import geolocate_ip
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "fail"}
    mock_response.raise_for_status = MagicMock()
    with patch("tracr.geo.ipgeo.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(get=AsyncMock(return_value=mock_response))
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        result = await geolocate_ip("0.0.0.0")
    assert result is None


@pytest.mark.asyncio
async def test_geoparse_text_parses_response():
    from tracr.geo.geoparser import geoparse_text
    mock_response = MagicMock()
    mock_response.json.return_value = [{
        "word": "Kigali", "score": 0.95,
        "geo": {"lat": "-1.94995", "lon": "30.05885", "country_code3": "RWA", "geonameid": "202061"},
    }]
    mock_response.raise_for_status = MagicMock()
    with patch("tracr.geo.geoparser.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(post=AsyncMock(return_value=mock_response))
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        result = await geoparse_text("The summit was held in Kigali.")
    assert len(result) == 1
    assert result[0].place_name == "Kigali"
    assert result[0].latitude == -1.94995
    assert result[0].country_code == "RWA"


@pytest.mark.asyncio
async def test_geoparse_text_returns_empty_when_unavailable():
    from tracr.geo.geoparser import geoparse_text
    import httpx
    with patch("tracr.geo.geoparser.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            side_effect=httpx.ConnectError("connection refused")
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        result = await geoparse_text("Fighting near Goma intensified.")
    assert result == []


@pytest.mark.asyncio
async def test_geoparse_empty_text():
    from tracr.geo.geoparser import geoparse_text
    assert await geoparse_text("") == []


def test_location_event_model_importable():
    from tracr.db.models import LocationEvent, GeoSourceType
    assert GeoSourceType.exif == "exif"
    assert GeoSourceType.ip_geo == "ip_geo"
    assert GeoSourceType.mordecai3 == "mordecai3"


def test_geolocate_document_task_registered():
    from tracr.tasks import celery_app
    assert "tracr.tasks.geo.geolocate_document" in celery_app.tasks


def test_geo_queue_in_task_routes():
    from tracr.tasks import celery_app
    routes = celery_app.conf.task_routes
    assert any("geo" in str(v) for v in routes.values())
