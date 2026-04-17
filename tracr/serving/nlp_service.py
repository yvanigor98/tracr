"""
BentoML NLP service — wraps spaCy NER pipeline.

Exposes:
  POST /extract   {"text": "..."}  →  [{"text": ..., "entity_type": ..., ...}]
  GET  /healthz                    →  {"status": "ok"}
"""
from __future__ import annotations

import spacy
from dataclasses import dataclass
from typing import List

import bentoml
from pydantic import BaseModel

ENTITY_TYPES = {"PERSON", "ORG", "GPE", "LOC", "DATE", "EMAIL", "URL"}
CONTEXT_WINDOW = 100


class ExtractRequest(BaseModel):
    text: str


class MentionResponse(BaseModel):
    text: str
    entity_type: str
    char_start: int
    char_end: int
    snippet: str
    score: float


TYPE_WEIGHTS = {
    "PERSON": 1.0,
    "ORG": 0.9,
    "GPE": 0.8,
    "LOC": 0.7,
    "DATE": 0.4,
    "EMAIL": 1.0,
    "URL": 0.5,
}


@bentoml.service(
    name="tracr-nlp",
    resources={"cpu": "2"},
    traffic={"timeout": 30},
)
class NLPService:
    def __init__(self) -> None:
        self._model_name = "en_core_web_trf"
        self._nlp = spacy.load(self._model_name)

    @bentoml.api
    def extract(self, request: ExtractRequest) -> List[MentionResponse]:
        """Extract named entities from text."""
        if not request.text or not request.text.strip():
            return []

        doc = self._nlp(request.text)
        mentions = []

        for ent in doc.ents:
            if ent.label_ not in ENTITY_TYPES:
                continue
            start = max(0, ent.start_char - CONTEXT_WINDOW)
            end = min(len(request.text), ent.end_char + CONTEXT_WINDOW)
            snippet = request.text[start:end].strip()
            score = TYPE_WEIGHTS.get(ent.label_, 0.5)
            mentions.append(MentionResponse(
                text=ent.text,
                entity_type=ent.label_.lower(),
                char_start=ent.start_char,
                char_end=ent.end_char,
                snippet=snippet,
                score=score,
            ))

        return mentions

    @bentoml.api
    def healthz(self) -> dict:
        """Health check — confirms model is loaded."""
        return {"status": "ok", "model": self._model_name}


svc = NLPService
