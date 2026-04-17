"""
Graph sync — reads entities + mentions from Postgres,
writes nodes and CO_OCCURS relationships to Neo4j.
"""
from __future__ import annotations

import uuid
from collections import defaultdict

import structlog
from neo4j import AsyncDriver
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tracr.config import settings
from tracr.db.models import Entity, Mention

logger = structlog.get_logger()


def _pg_session():
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False), engine


async def sync_entities(driver: AsyncDriver) -> dict:
    """
    Full sync:
    1. Upsert all Entity rows as Neo4j nodes.
    2. For each document, create CO_OCCURS edges between every
       pair of entities that appear in the same document.
    """
    SessionLocal, engine = _pg_session()
    try:
        async with SessionLocal() as db:
            # Load all entities
            entities = (await db.execute(select(Entity))).scalars().all()

            # Load mentions grouped by document
            rows = (await db.execute(
                select(Mention.document_id, Mention.entity_id)
            )).fetchall()

    finally:
        await engine.dispose()

    # Build doc → [entity_ids] map
    doc_entities: dict[str, list[str]] = defaultdict(list)
    for doc_id, entity_id in rows:
        doc_entities[str(doc_id)].append(str(entity_id))

    upserted_nodes = 0
    upserted_edges = 0

    async with driver.session() as session:
        # Upsert entity nodes
        for entity in entities:
            await session.run(
                """
                MERGE (e:Entity {entity_id: $entity_id})
                SET e.canonical_name = $canonical_name,
                    e.entity_type    = $entity_type,
                    e.aliases        = $aliases,
                    e.confidence     = $confidence
                """,
                entity_id=str(entity.id),
                canonical_name=entity.canonical_name,
                entity_type=entity.entity_type,
                aliases=entity.aliases or [],
                confidence=float(entity.confidence),
            )
            upserted_nodes += 1

        # Upsert CO_OCCURS edges
        for doc_id, entity_ids in doc_entities.items():
            # Deduplicate within document
            unique_ids = list(set(entity_ids))
            for i in range(len(unique_ids)):
                for j in range(i + 1, len(unique_ids)):
                    await session.run(
                        """
                        MATCH (a:Entity {entity_id: $id_a})
                        MATCH (b:Entity {entity_id: $id_b})
                        MERGE (a)-[r:CO_OCCURS]-(b)
                        ON CREATE SET r.weight = 1, r.documents = [$doc_id]
                        ON MATCH SET  r.weight = r.weight + 1,
                                      r.documents = r.documents + [$doc_id]
                        """,
                        id_a=unique_ids[i],
                        id_b=unique_ids[j],
                        doc_id=doc_id,
                    )
                    upserted_edges += 1

    logger.info("graph.sync_complete",
                nodes=upserted_nodes, edges=upserted_edges)
    return {"nodes": upserted_nodes, "edges": upserted_edges}
