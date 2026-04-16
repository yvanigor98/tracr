from fastapi import APIRouter, HTTPException

from tracr.api.schemas import JobStatusResponse, JobTriggerRequest
from tracr.tasks.ingestion import celery_app, ingest_source

router = APIRouter()


@router.post("/trigger", response_model=JobStatusResponse, status_code=202)
async def trigger_ingestion(payload: JobTriggerRequest):
    task = ingest_source.delay(str(payload.source_id))
    return JobStatusResponse(
        job_id=task.id,
        status="queued",
        result={"source_id": str(payload.source_id)},
    )


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    task = celery_app.AsyncResult(job_id)

    if task.state == "PENDING":
        return JobStatusResponse(job_id=job_id, status="pending")
    elif task.state == "SUCCESS":
        return JobStatusResponse(job_id=job_id, status="success", result=task.result)
    elif task.state == "FAILURE":
        return JobStatusResponse(
            job_id=job_id, status="failed", error=str(task.result)
        )
    return JobStatusResponse(job_id=job_id, status=task.state.lower())
