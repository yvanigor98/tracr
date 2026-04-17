import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Float, ForeignKey,
    Index, Integer, String, Text, UniqueConstraint,
    func, text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SourceType(str, PyEnum):
    rss = "rss"
    api = "api"
    scraper = "scraper"
    tor = "tor"


class ProcessingStatus(str, PyEnum):
    pending = "pending"
    processing = "processing"
    done = "done"
    failed = "failed"


class EntityType(str, PyEnum):
    person = "person"
    org = "org"
    location = "location"
    other = "other"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[SourceType] = mapped_column(String(50), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    schedule_cron: Mapped[str | None] = mapped_column(String(100), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_fetched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    documents: Mapped[list["RawDocument"]] = relationship(
        back_populates="source", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_sources_type", "type"),
        Index("ix_sources_active", "active"),
    )


class RawDocument(Base):
    __tablename__ = "raw_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        String(50), default=ProcessingStatus.pending, nullable=False
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
    )

    source: Mapped["Source"] = relationship(back_populates="documents")
    mentions: Mapped[list["Mention"]] = relationship(
        back_populates="document", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("url_hash", name="uq_raw_documents_url_hash"),
        Index("ix_raw_documents_processing_status", "processing_status"),
        Index("ix_raw_documents_source_id", "source_id"),
        Index("ix_raw_documents_fetched_at", "fetched_at"),
    )


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    canonical_name: Mapped[str] = mapped_column(String(512), nullable=False)
    entity_type: Mapped[EntityType] = mapped_column(String(50), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    first_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    mentions: Mapped[list["Mention"]] = relationship(
        back_populates="entity", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_entities_canonical_name", "canonical_name"),
        Index("ix_entities_entity_type", "entity_type"),
        Index("ix_entities_confidence", "confidence"),
    )


class Mention(Base):
    __tablename__ = "mentions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("raw_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    char_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    entity: Mapped["Entity"] = relationship(back_populates="mentions")
    document: Mapped["RawDocument"] = relationship(back_populates="mentions")

    __table_args__ = (
        Index("ix_mentions_entity_id", "entity_id"),
        Index("ix_mentions_document_id", "document_id"),
        Index("ix_mentions_score", "score"),
    )


class GeoSourceType(str, PyEnum):
    exif = "exif"
    ip_geo = "ip_geo"
    mordecai3 = "mordecai3"
    manual = "manual"


class LocationEvent(Base):
    __tablename__ = "location_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=True
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("raw_documents.id", ondelete="CASCADE"), nullable=True
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    place_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    geo_source: Mapped[GeoSourceType] = mapped_column(
        String(20), nullable=False, default=GeoSourceType.mordecai3
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    raw_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    observed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_location_events_entity_id", "entity_id"),
        Index("ix_location_events_document_id", "document_id"),
        Index("ix_location_events_geo_source", "geo_source"),
    )
