"""
Neo4j schema initialisation — constraints and indexes.
Run once at startup.
"""
from __future__ import annotations

import structlog
from neo4j import AsyncDriver

logger = structlog.get_logger()

CONSTRAINTS = [
    # Each Entity node is uniquely identified by its Postgres UUID
    "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS "
    "FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE",
]

INDEXES = [
    "CREATE INDEX entity_type_idx IF NOT EXISTS "
    "FOR (e:Entity) ON (e.entity_type)",

    "CREATE INDEX entity_name_idx IF NOT EXISTS "
    "FOR (e:Entity) ON (e.canonical_name)",
]


async def init_schema(driver: AsyncDriver) -> None:
    """Apply constraints and indexes. Idempotent."""
    async with driver.session() as session:
        for stmt in CONSTRAINTS + INDEXES:
            await session.run(stmt)
    logger.info("graph.schema_initialised")
