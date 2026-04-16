import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tracr.api.routers import entities, jobs, sources

logger = structlog.get_logger()

app = FastAPI(
    title="Tracr",
    description="Open-source OSINT intelligence platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(entities.router, prefix="/entities", tags=["entities"])
app.include_router(sources.router, prefix="/sources", tags=["sources"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "tracr"}


@app.on_event("startup")
async def startup():
    logger.info("tracr.startup", version="0.1.0")


@app.on_event("shutdown")
async def shutdown():
    logger.info("tracr.shutdown")
