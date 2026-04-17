"""Tests for BentoML NLP service and updated processor HTTP integration."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tracr.processing.ner import ExtractedMention

# Skip service-level tests if bentoml is not installed on the host.
# bentoml lives in the Docker image only — these tests validate the
# service contract and run in CI inside the container.
bentoml = pytest.importorskip("bentoml", reason="bentoml not installed on host")


# ---------------------------------------------------------------------------
# NLP service unit tests (skipped on host if bentoml absent)
# ---------------------------------------------------------------------------

def test_nlp_service_imports():
    """NLP service module imports without error."""
    from tracr.serving import nlp_service
    assert hasattr(nlp_service, "NLPService")
    assert hasattr(nlp_service, "ExtractRequest")
    assert hasattr(nlp_service, "MentionResponse")


def test_extract_request_schema():
    """ExtractRequest validates text field."""
    from tracr.serving.nlp_service import ExtractRequest
    req = ExtractRequest(text="Julius Malema spoke in Johannesburg.")
    assert req.text == "Julius Malema spoke in Johannesburg."


def test_mention_response_schema():
    """MentionResponse validates all fields."""
    from tracr.serving.nlp_service import MentionResponse
    m = MentionResponse(
        text="Julius Malema",
        entity_type="person",
        char_start=0,
        char_end=13,
        snippet="Julius Malema spoke in Johannesburg.",
        score=1.0,
    )
    assert m.text == "Julius Malema"
    assert m.score == 1.0


def test_nlp_service_extract_delegates_to_pipeline():
    """NLPService.extract calls NERPipeline and maps results correctly."""
    from tracr.serving.nlp_service import NLPService, ExtractRequest

    fake_mention = ExtractedMention(
        text="Nigeria",
        entity_type="gpe",
        char_start=0,
        char_end=7,
        snippet="Nigeria signed the agreement.",
        score=0.8,
    )

    svc = NLPService.__new__(NLPService)
    svc._pipeline = MagicMock()
    svc._pipeline.model = "en_core_web_trf"
    svc._pipeline.extract.return_value = [fake_mention]

    result = svc.extract(ExtractRequest(text="Nigeria signed the agreement."))

    assert len(result) == 1
    assert result[0].text == "Nigeria"
    assert result[0].entity_type == "gpe"
    assert result[0].score == 0.8


def test_nlp_service_healthz():
    """NLPService.healthz returns status ok and model name."""
    from tracr.serving.nlp_service import NLPService

    svc = NLPService.__new__(NLPService)
    svc._pipeline = MagicMock()
    svc._pipeline.model = "en_core_web_trf"

    result = svc.healthz()
    assert result["status"] == "ok"
    assert result["model"] == "en_core_web_trf"
