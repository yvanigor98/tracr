"""
Graph API router — entity relationship queries via Neo4j.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from tracr.graph.driver import get_driver

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/neighbours/{entity_id}")
async def get_neighbours(entity_id: str, limit: int = 10):
    """
    Return entities that co-occur with the given entity,
    ordered by co-occurrence weight descending.
    """
    driver = await get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (e:Entity {entity_id: $entity_id})-[r:CO_OCCURS]-(n:Entity)
            RETURN n.entity_id      AS entity_id,
                   n.canonical_name AS canonical_name,
                   n.entity_type    AS entity_type,
                   r.weight         AS weight
            ORDER BY r.weight DESC
            LIMIT $limit
            """,
            entity_id=entity_id,
            limit=limit,
        )
        records = await result.data()

    if not records:
        return {"entity_id": entity_id, "neighbours": []}

    return {
        "entity_id": entity_id,
        "neighbours": records,
    }


@router.get("/path")
async def shortest_path(from_id: str, to_id: str):
    """
    Return the shortest co-occurrence path between two entities.
    """
    driver = await get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH p = shortestPath(
                (a:Entity {entity_id: $from_id})-[*]-(b:Entity {entity_id: $to_id})
            )
            RETURN [node IN nodes(p) | {
                entity_id:      node.entity_id,
                canonical_name: node.canonical_name,
                entity_type:    node.entity_type
            }] AS path,
            length(p) AS hops
            """,
            from_id=from_id,
            to_id=to_id,
        )
        record = await result.single()

    if not record:
        raise HTTPException(status_code=404, detail="No path found between entities")

    return {"path": record["path"], "hops": record["hops"]}
