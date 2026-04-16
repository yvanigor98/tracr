from tracr.tasks.ingestion import celery_app
from tracr.tasks import processing  # noqa: F401 - registers tasks with celery
from tracr.tasks import scheduler   # noqa: F401 - registers beat tasks with celery

__all__ = ["celery_app"]
