import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# --- Source schemas ---
class SourceBase(BaseModel):
    name: str
    type: str
    url: str
    schedule_cron: str | None = None
    active: bool = True
    config: dict = Field(default_factory=dict)


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    schedule_cron: str | None = None
    active: bool | None = None
    config: dict | None = None


class SourceResponse(SourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    last_fetched_at: datetime | None
    created_at: datetime
    updated_at: datetime


# --- Entity schemas ---
class EntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    canonical_name: str
    entity_type: str
    aliases: list[str]
    confidence: float
    first_seen: datetime | None
    last_seen: datetime | None
    metadata_: dict = Field(alias="metadata_")


class EntitySearchResponse(BaseModel):
    items: list[EntityResponse]
    total: int
    cursor: str | None = None


# --- Mention schemas ---
class MentionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_id: uuid.UUID
    document_id: uuid.UUID
    snippet: str | None
    score: float
    created_at: datetime


class MentionListResponse(BaseModel):
    items: list[MentionResponse]
    total: int
    cursor: str | None = None


# --- Job schemas ---
class JobTriggerRequest(BaseModel):
    source_id: uuid.UUID


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: dict | None = None
    error: str | None = None
