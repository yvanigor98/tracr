"""Tests for Celery Beat scheduler task."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def test_beat_schedule_registered():
    """Beat schedule has both expected periodic tasks."""
    from tracr.tasks import celery_app

    schedule = celery_app.conf.beat_schedule
    assert "ingest-all-sources-every-15-minutes" in schedule
    assert "process-pending-documents-every-5-minutes" in schedule

    assert schedule["ingest-all-sources-every-15-minutes"]["task"] == \
        "tracr.tasks.scheduler.ingest_all_sources"
    assert schedule["ingest-all-sources-every-15-minutes"]["schedule"] == 900.0
    assert schedule["process-pending-documents-every-5-minutes"]["schedule"] == 300.0


def test_ingest_all_sources_dispatches_tasks():
    """ingest_all_sources fans out one ingest_source task per active source."""
    from tracr.tasks.scheduler import ingest_all_sources

    fake_ids = ["uuid-aaa", "uuid-bbb", "uuid-ccc"]

    with patch(
        "tracr.tasks.scheduler._fetch_active_source_ids",
        new=AsyncMock(return_value=fake_ids),
    ), patch(
        "tracr.tasks.ingestion.ingest_source.apply_async"
    ) as mock_apply:
        result = ingest_all_sources()

    assert result == {"dispatched": 3}
    assert mock_apply.call_count == 3
    calls = [c.kwargs["args"][0] for c in mock_apply.call_args_list]
    assert calls == fake_ids


def test_ingest_all_sources_empty():
    """ingest_all_sources handles zero active sources gracefully."""
    from tracr.tasks.scheduler import ingest_all_sources

    with patch(
        "tracr.tasks.scheduler._fetch_active_source_ids",
        new=AsyncMock(return_value=[]),
    ), patch(
        "tracr.tasks.ingestion.ingest_source.apply_async"
    ) as mock_apply:
        result = ingest_all_sources()

    assert result == {"dispatched": 0}
    mock_apply.assert_not_called()
