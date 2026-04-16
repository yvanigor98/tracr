from fastapi import APIRouter, HTTPException

from tracr.api.schemas import JobStatusResponse, JobTriggerRequest

router = APIRouter()


@router.post("/trigger", response_model=JobStatusResponse, status_code=202)
async def trigger_ingestion(payload: JobTriggerRequest):
    # Celery task wiring comes in next step
    # For now return a placeholder so the endpoint is testable
    return JobStatusResponse(
        job_id="placeholder",
        status="queued",
        result={"source_id": str(payload.source_id)},
    )


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    # Celery result backend wiring comes in next step
    if job_id == "placeholder":
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(job_id=job_id, status="unknown")
