"""
PostGIS pattern-of-life clustering.
Uses ST_ClusterDBSCAN to group location events per entity
into spatial clusters — reveals where an entity operates.
"""
from __future__ import annotations

from dataclasses import dataclass

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tracr.config import settings

logger = structlog.get_logger()


@dataclass
class LocationCluster:
    entity_id: str
    cluster_id: int
    centroid_lat: float
    centroid_lon: float
    event_count: int
    place_names: list[str]


def _pg_session():
    engine = create_async_engine(
        settings.DATABASE_URL, pool_size=5, max_overflow=10, pool_pre_ping=True
    )
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False), engine


async def cluster_entity_locations(
    entity_id: str,
    eps_km: float = 50.0,
    min_points: int = 2,
) -> list[LocationCluster]:
    """
    Run DBSCAN clustering on all location events for an entity.

    eps_km: cluster radius in kilometres (default 50km)
    min_points: minimum events to form a cluster (default 2)
    """
    # Convert km to degrees (approximate: 1 degree ≈ 111km)
    eps_degrees = eps_km / 111.0

    SessionLocal, engine = _pg_session()
    try:
        async with SessionLocal() as db:
            result = await db.execute(
                text("""
                    SELECT
                        cluster_id,
                        COUNT(*)                            AS event_count,
                        AVG(latitude)                       AS centroid_lat,
                        AVG(longitude)                      AS centroid_lon,
                        ARRAY_AGG(DISTINCT place_name)      AS place_names
                    FROM (
                        SELECT
                            latitude,
                            longitude,
                            place_name,
                            ST_ClusterDBSCAN(
                                ST_SetSRID(ST_MakePoint(longitude, latitude), 4326),
                                :eps,
                                :min_pts
                            ) OVER (PARTITION BY entity_id) AS cluster_id
                        FROM location_events
                        WHERE entity_id = :entity_id
                          AND latitude  IS NOT NULL
                          AND longitude IS NOT NULL
                    ) sub
                    WHERE cluster_id IS NOT NULL
                    GROUP BY cluster_id
                    ORDER BY event_count DESC
                """),
                {
                    "entity_id": entity_id,
                    "eps": eps_degrees,
                    "min_pts": min_points,
                },
            )
            rows = result.fetchall()
    finally:
        await engine.dispose()

    clusters = []
    for row in rows:
        clusters.append(LocationCluster(
            entity_id=entity_id,
            cluster_id=row.cluster_id,
            centroid_lat=float(row.centroid_lat),
            centroid_lon=float(row.centroid_lon),
            event_count=int(row.event_count),
            place_names=[p for p in (row.place_names or []) if p],
        ))

    logger.info("cluster.complete", entity_id=entity_id, clusters=len(clusters))
    return clusters
