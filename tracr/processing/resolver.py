import re
import structlog
from dataclasses import dataclass

logger = structlog.get_logger()


@dataclass
class ResolvedEntity:
    canonical_name: str
    entity_type: str
    aliases: list[str]
    confidence: float


def normalize_name(name: str) -> str:
    """Normalize entity name for comparison."""
    name = name.strip()
    name = re.sub(r'\s+', ' ', name)
    return name.lower()


def similarity(a: str, b: str) -> float:
    """Simple Jaro-Winkler-like similarity for entity matching."""
    a, b = normalize_name(a), normalize_name(b)
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.9

    # Token overlap
    tokens_a = set(a.split())
    tokens_b = set(b.split())
    if not tokens_a or not tokens_b:
        return 0.0

    overlap = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return overlap / union


def resolve_entities(
    mentions: list[tuple[str, str]],
    threshold: float = 0.85,
) -> list[ResolvedEntity]:
    """
    Group mention (text, type) pairs into resolved entities.
    Same type + similarity above threshold = same entity.
    """
    clusters: list[ResolvedEntity] = []

    for text, entity_type in mentions:
        matched = False

        for cluster in clusters:
            if cluster.entity_type != entity_type:
                continue
            sim = similarity(text, cluster.canonical_name)
            if sim >= threshold:
                if text not in cluster.aliases:
                    cluster.aliases.append(text)
                cluster.confidence = min(1.0, cluster.confidence + 0.05)
                matched = True
                break

        if not matched:
            clusters.append(ResolvedEntity(
                canonical_name=text,
                entity_type=entity_type,
                aliases=[text],
                confidence=0.7,
            ))

    return clusters
