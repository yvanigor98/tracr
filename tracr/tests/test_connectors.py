"""Tests for WHOIS and Shodan connectors."""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest


# ---------------------------------------------------------------------------
# WHOIS
# ---------------------------------------------------------------------------

def test_is_ip_detection():
    from tracr.ingestion.fetchers.shodan import _is_ip
    assert _is_ip("8.8.8.8") is True
    assert _is_ip("192.168.1.1") is True
    assert _is_ip("example.com") is False
    assert _is_ip("sub.domain.co.uk") is False


@pytest.mark.asyncio
async def test_fetch_whois_returns_document():
    from tracr.ingestion.fetchers.whois import fetch_whois

    mock_result = MagicMock()
    mock_result.domain_name = "example.com"
    mock_result.registrar = "Test Registrar Inc."
    mock_result.org = "Example Org"
    mock_result.country = "US"
    mock_result.emails = ["admin@example.com"]
    mock_result.name_servers = ["ns1.example.com", "ns2.example.com"]
    mock_result.status = "active"
    mock_result.creation_date = None
    mock_result.expiration_date = None
    mock_result.updated_date = None
    mock_result.name = "John Doe"

    with patch("tracr.ingestion.fetchers.whois.whois.whois", return_value=mock_result):
        docs = await fetch_whois("source-1", "example.com")

    assert len(docs) == 1
    doc = docs[0]
    assert doc.url == "whois://example.com"
    assert doc.title == "WHOIS: example.com"
    assert "Example Org" in doc.body
    assert doc.metadata["registrar"] == "Test Registrar Inc."
    assert doc.metadata["country"] == "US"


@pytest.mark.asyncio
async def test_fetch_whois_returns_empty_on_no_data():
    from tracr.ingestion.fetchers.whois import fetch_whois

    mock_result = MagicMock()
    mock_result.domain_name = None

    with patch("tracr.ingestion.fetchers.whois.whois.whois", return_value=mock_result):
        docs = await fetch_whois("source-1", "notadomain")

    assert docs == []


@pytest.mark.asyncio
async def test_fetch_whois_returns_empty_on_exception():
    from tracr.ingestion.fetchers.whois import fetch_whois

    with patch("tracr.ingestion.fetchers.whois.whois.whois", side_effect=Exception("timeout")):
        docs = await fetch_whois("source-1", "example.com")

    assert docs == []


# ---------------------------------------------------------------------------
# Shodan
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_shodan_returns_empty_without_api_key():
    from tracr.ingestion.fetchers.shodan import fetch_shodan

    with patch("tracr.ingestion.fetchers.shodan.settings") as mock_settings:
        mock_settings.SHODAN_API_KEY = ""
        docs = await fetch_shodan("source-1", "8.8.8.8")

    assert docs == []


@pytest.mark.asyncio
async def test_fetch_shodan_returns_document_for_ip():
    from tracr.ingestion.fetchers.shodan import fetch_shodan

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ip_str": "8.8.8.8",
        "org": "Google LLC",
        "country_name": "United States",
        "isp": "Google",
        "os": None,
        "ports": [53, 443],
        "hostnames": ["dns.google"],
        "vulns": {},
        "data": [
            {"port": 53, "transport": "udp", "product": "Google DNS", "version": None, "cpe": None}
        ],
        "last_update": "2024-01-01",
    }
    mock_response.raise_for_status = MagicMock()

    with patch("tracr.ingestion.fetchers.shodan.settings") as mock_settings,          patch("tracr.ingestion.fetchers.shodan.httpx.AsyncClient") as mock_client:
        mock_settings.SHODAN_API_KEY = "test-key"
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(get=AsyncMock(return_value=mock_response))
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        docs = await fetch_shodan("source-1", "8.8.8.8")

    assert len(docs) == 1
    doc = docs[0]
    assert doc.url == "shodan://8.8.8.8"
    assert doc.title == "Shodan: 8.8.8.8"
    assert "Google LLC" in doc.body
    assert 53 in doc.metadata["ports"]
    assert "dns.google" in doc.metadata["hostnames"]


@pytest.mark.asyncio
async def test_fetch_shodan_returns_empty_on_404():
    from tracr.ingestion.fetchers.shodan import fetch_shodan

    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch("tracr.ingestion.fetchers.shodan.settings") as mock_settings,          patch("tracr.ingestion.fetchers.shodan.httpx.AsyncClient") as mock_client:
        mock_settings.SHODAN_API_KEY = "test-key"
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(get=AsyncMock(return_value=mock_response))
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        docs = await fetch_shodan("source-1", "1.2.3.4")

    assert docs == []


# ---------------------------------------------------------------------------
# SourceType enum
# ---------------------------------------------------------------------------

def test_source_type_has_whois_and_shodan():
    from tracr.db.models import SourceType
    assert SourceType.whois == "whois"
    assert SourceType.shodan == "shodan"


# ---------------------------------------------------------------------------
# ingest_source routing
# ---------------------------------------------------------------------------

def test_ingest_source_routes_whois():
    """ingest_source task file contains whois routing."""
    content = open("tracr/tasks/ingestion.py").read()
    assert "fetch_whois" in content
    assert "source.type == \"whois\"" in content


def test_ingest_source_routes_shodan():
    """ingest_source task file contains shodan routing."""
    content = open("tracr/tasks/ingestion.py").read()
    assert "fetch_shodan" in content
    assert "source.type == \"shodan\"" in content
