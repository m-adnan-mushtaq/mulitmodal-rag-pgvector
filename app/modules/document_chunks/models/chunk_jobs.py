import uuid
from datetime import datetime
from sqlalchemy import (
    String,
    Text,
    ForeignKey,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_table import BaseTable
from app.modules.source_documents.models.source_document import SourceDocument


class ChunkJob(BaseTable):
    __tablename__ = "chunk_jobs"

    source_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_documents.id", ondelete="CASCADE"), nullable=True
    )
    
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="processing")
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    source_document = relationship(SourceDocument, back_populates="chunk_jobs", foreign_keys=[source_document_id])
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    created_by = relationship("User", back_populates="chunk_jobs", foreign_keys=[created_by_id])
    
    document_chunks = relationship(
        "DocumentChunk",
        back_populates="chunk_job",
        foreign_keys="DocumentChunk.chunk_job_id",
    )