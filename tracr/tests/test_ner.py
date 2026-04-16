import pytest
from tracr.processing.ner import NERPipeline


@pytest.fixture
def ner():
    return NERPipeline(model="en_core_web_sm")


def test_extract_person(ner):
    text = "Julius Malema was sentenced to five years in prison in South Africa."
    mentions = ner.extract(text)
    types = [m.entity_type for m in mentions]
    texts = [m.text for m in mentions]
    assert "person" in types
    assert any("Malema" in t for t in texts)


def test_extract_gpe(ner):
    text = "Nigeria and South Africa signed a trade agreement in Lagos."
    mentions = ner.extract(text)
    types = [m.entity_type for m in mentions]
    assert "gpe" in types


def test_extract_empty_text(ner):
    mentions = ner.extract("")
    assert mentions == []


def test_extract_no_entities(ner):
    mentions = ner.extract("The quick brown fox jumps over the lazy dog.")
    assert isinstance(mentions, list)


def test_mention_has_snippet(ner):
    text = "President Kagame spoke at the African Union summit in Addis Ababa."
    mentions = ner.extract(text)
    for mention in mentions:
        assert mention.snippet is not None
        assert len(mention.snippet) > 0


def test_mention_score_range(ner):
    text = "Kenya's Eliud Kipchoge won the Berlin Marathon in 2023."
    mentions = ner.extract(text)
    for mention in mentions:
        assert 0.0 <= mention.score <= 1.0
