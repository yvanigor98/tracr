"""Tests for Neo4j graph module."""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest


def test_neo4j_config_fields():
    """Settings has Neo4j fields with correct defaults."""
    from tracr.config import settings
    assert settings.NEO4J_URI == "bolt://neo4j:7687"
    assert settings.NEO4J_USER == "neo4j"
    assert settings.NEO4J_PASSWORD == "tracr-neo4j"


@pytest.mark.asyncio
async def test_init_schema_runs_all_statements():
    """init_schema executes all constraints and indexes."""
    from tracr.graph.schema import init_schema, CONSTRAINTS, INDEXES

    mock_session = AsyncMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_driver.session.return_value.__aexit__ = AsyncMock(return_value=False)

    await init_schema(mock_driver)

    assert mock_session.run.call_count == len(CONSTRAINTS) + len(INDEXES)


@pytest.mark.asyncio
async def test_sync_entities_upserts_nodes():
    """sync_entities upserts entity nodes into Neo4j."""
    from tracr.graph.sync import sync_entities
    import uuid

    mock_entity = MagicMock()
    mock_entity.id = uuid.uuid4()
    mock_entity.canonical_name = "Julius Malema"
    mock_entity.entity_type = "person"
    mock_entity.aliases = ["Malema", "Julius"]
    mock_entity.confidence = 0.9

    mock_session = AsyncMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_driver.session.return_value.__aexit__ = AsyncMock(return_value=False)

    # Build a synchronous session factory mock
    mock_db = AsyncMock()
    mock_entities_result = MagicMock()
    mock_entities_result.scalars.return_value.all.return_value = [mock_entity]
    mock_mentions_result = MagicMock()
    mock_mentions_result.fetchall.return_value = []
    mock_db.execute = AsyncMock(
        side_effect=[mock_entities_result, mock_mentions_result]
    )

    mock_sf = MagicMock()  # synchronous factory callable
    mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_db)
    mock_sf.return_value.__aexit__ = AsyncMock(return_value=False)

    mock_engine = AsyncMock()

    with patch("tracr.graph.sync._pg_session", return_value=(mock_sf, mock_engine)):
        result = await sync_entities(mock_driver)

    assert result["nodes"] == 1
    assert result["edges"] == 0
    assert mock_session.run.call_count >= 1


@pytest.mark.asyncio
async def test_get_neighbours_returns_empty_for_unknown_entity():
    """get_neighbours returns empty list when entity has no connections."""
    from tracr.api.routers.graph import get_neighbours

    mock_result = AsyncMock()
    mock_result.data = AsyncMock(return_value=[])
    mock_session = AsyncMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_driver = MagicMock()
    mock_driver.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_driver.session.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch("tracr.api.routers.graph.get_driver", AsyncMock(return_value=mock_driver)):
        result = await get_neighbours("unknown-id")

    assert result == {"entity_id": "unknown-id", "neighbours": []}


@pytest.mark.asyncio
async def test_get_neighbours_returns_records():
    """get_neighbours returns co-occurring entities ordered by weight."""
    from tracr.api.routers.graph import get_neighbours

    fake_records = [
        {"entity_id": "abc", "canonical_name": "Sudan", "entity_type": "gpe", "weight": 5},
        {"entity_id": "def", "canonical_name": "Nigeria", "entity_type": "gpe", "weight": 3},
    ]

    mock_result = AsyncMock()
    mock_result.data = AsyncMock(return_value=fake_records)
    mock_session = AsyncMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_driver = MagicMock()
    mock_driver.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_driver.session.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch("tracr.api.routers.graph.get_driver", AsyncMock(return_value=mock_driver)):
        result = await get_neighbours("entity-123", limit=10)

    assert len(result["neighbours"]) == 2
    assert result["neighbours"][0]["canonical_name"] == "Sudan"


def test_sync_graph_task_registered():
    """sync_graph task is registered with Celery."""
    from tracr.tasks import celery_app
    assert "tracr.tasks.graph.sync_graph" in celery_app.tasks


def test_sync_graph_beat_schedule():
    """sync_graph is in the beat schedule."""
    from tracr.tasks import celery_app
    schedule = celery_app.conf.beat_schedule
    assert "sync-graph-every-30-minutes" in schedule
    assert schedule["sync-graph-every-30-minutes"]["schedule"] == 1800.0
