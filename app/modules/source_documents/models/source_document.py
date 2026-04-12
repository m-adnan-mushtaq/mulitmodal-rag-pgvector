import uuid
from datetime import datetime
from sqlalchemy import (
    String,
    Integer,
    Boolean,
    Text,
    ForeignKey,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_table import BaseTable


class SourceDocument(BaseTable):
    __tablename__ = "source_documents"

    media_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media.id", ondelete="SET NULL"), nullable=True
    )

    ingestion_type: Mapped[str] = mapped_column(String(32), nullable=True, default="file")
    ingestion_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    title: Mapped[str] = mapped_column(String(512), nullable=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=True)  # pdf, spec, manual, code
    layer_type: Mapped[str] = mapped_column(String(32), nullable=True)  # GLOBAL, COMPANY, PROJECT

    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Scenario / metadata (optional, indexed for filtering)
    trade: Mapped[str | None] = mapped_column(String(255), nullable=True)
    division: Mapped[str | None] = mapped_column(String(255), nullable=True)
    system: Mapped[str | None] = mapped_column(String(255), nullable=True)
    region: Mapped[str | None] = mapped_column(String(255), nullable=True)
    building_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    project_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phase: Mapped[str | None] = mapped_column(String(255), nullable=True)
    site_conditions: Mapped[str | None] = mapped_column(String(255), nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String(255), nullable=True)
    constraints: Mapped[str | None] = mapped_column(String(512), nullable=True)

    total_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parsed_text: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="processing")
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    root_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    parent_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_documents.id", ondelete="SET NULL"), nullable=True
    )

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )

    # Relationships
    media = relationship("Media", back_populates="source_documents", foreign_keys=[media_id])
    creator = relationship("User", back_populates="source_documents", foreign_keys=[created_by])
    parent = relationship(
        "SourceDocument",
        remote_side="SourceDocument.id",
        back_populates="children",
        foreign_keys=[parent_document_id],
    )
    children = relationship(
        "SourceDocument",
        back_populates="parent",
        foreign_keys=[parent_document_id],
    )
    chunk_jobs = relationship(
        "ChunkJob",
        back_populates="source_document",
        foreign_keys="ChunkJob.source_document_id",
    )
    document_chunks = relationship(
        "DocumentChunk",
        back_populates="source_document",
        foreign_keys="DocumentChunk.source_document_id",
    )