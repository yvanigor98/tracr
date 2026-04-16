import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tracr.api.schemas import EntityResponse, EntitySearchResponse, MentionListResponse, MentionResponse
from tracr.db.models import Entity, Mention
from tracr.db.session import get_db

router = APIRouter()


@router.get("/search", response_model=EntitySearchResponse)
async def search_entities(
    q: str | None = Query(None, description="Search by name"),
    entity_type: str | None = Query(None, description="Filter by type"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Entity)

    if q:
        stmt = stmt.where(
            Entity.canonical_name.ilike(f"%{q}%")
        )
    if entity_type:
        stmt = stmt.where(Entity.entity_type == entity_type)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(count_stmt)

    stmt = stmt.offset(offset).limit(limit).order_by(Entity.confidence.desc())
    result = await db.execute(stmt)
    entities = result.scalars().all()

    return EntitySearchResponse(items=entities, total=total or 0)


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Entity).where(Entity.id == entity_id))
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.get("/{entity_id}/mentions", response_model=MentionListResponse)
async def get_entity_mentions(
    entity_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Mention).where(Mention.entity_id == entity_id)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(count_stmt)

    stmt = stmt.offset(offset).limit(limit).order_by(Mention.score.desc())
    result = await db.execute(stmt)
    mentions = result.scalars().all()

    return MentionListResponse(items=mentions, total=total or 0)
