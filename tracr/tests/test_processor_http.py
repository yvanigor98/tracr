"""Tests for processor HTTP integration with BentoML NLP service."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tracr.processing.ner import ExtractedMention


@pytest.mark.asyncio
async def test_call_nlp_service_parses_response():
    """call_nlp_service deserialises HTTP response into ExtractedMention list."""
    from tracr.processing.processor import call_nlp_service

    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "text": "Sudan",
            "entity_type": "gpe",
            "char_start": 0,
            "char_end": 5,
            "snippet": "Sudan peace talks collapsed.",
            "score": 0.8,
        }
    ]
    mock_response.raise_for_status = MagicMock()

    with patch("tracr.processing.processor.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(
                post=AsyncMock(return_value=mock_response)
            )
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await call_nlp_service("Sudan peace talks collapsed.")

    assert len(result) == 1
    assert result[0].text == "Sudan"
    assert result[0].entity_type == "gpe"


@pytest.mark.asyncio
async def test_call_nlp_service_empty_response():
    """call_nlp_service returns empty list when service finds no entities."""
    from tracr.processing.processor import call_nlp_service

    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status = MagicMock()

    with patch("tracr.processing.processor.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(
                post=AsyncMock(return_value=mock_response)
            )
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await call_nlp_service("12345 @@@ !!!")

    assert result == []
