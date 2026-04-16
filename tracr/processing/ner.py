import spacy
import structlog
from dataclasses import dataclass

logger = structlog.get_logger()

ENTITY_TYPES = {"PERSON", "ORG", "GPE", "LOC", "DATE", "EMAIL", "URL"}
CONTEXT_WINDOW = 100


@dataclass
class ExtractedMention:
    text: str
    entity_type: str
    char_start: int
    char_end: int
    snippet: str
    score: float


class NERPipeline:
    def __init__(self, model: str = "en_core_web_sm"):
        self.model = model
        self._nlp = None

    @property
    def nlp(self):
        if self._nlp is None:
            logger.info("ner.loading_model", model=self.model)
            self._nlp = spacy.load(self.model)
            logger.info("ner.model_loaded", model=self.model)
        return self._nlp

    def extract(self, text: str) -> list[ExtractedMention]:
        if not text or not text.strip():
            return []

        doc = self.nlp(text)
        mentions = []

        for ent in doc.ents:
            if ent.label_ not in ENTITY_TYPES:
                continue

            # Extract surrounding context
            start = max(0, ent.start_char - CONTEXT_WINDOW)
            end = min(len(text), ent.end_char + CONTEXT_WINDOW)
            snippet = text[start:end].strip()

            # Score based on entity type weight
            type_weights = {
                "PERSON": 1.0,
                "ORG": 0.9,
                "GPE": 0.8,
                "LOC": 0.7,
                "DATE": 0.4,
                "EMAIL": 1.0,
                "URL": 0.5,
            }
            score = type_weights.get(ent.label_, 0.5)

            mentions.append(ExtractedMention(
                text=ent.text,
                entity_type=ent.label_.lower(),
                char_start=ent.start_char,
                char_end=ent.end_char,
                snippet=snippet,
                score=score,
            ))

        return mentions


ner_pipeline = NERPipeline()
