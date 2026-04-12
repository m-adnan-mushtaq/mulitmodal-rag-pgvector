import uuid
from sqlalchemy import (
    Integer,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column,relationship
from pgvector.sqlalchemy import Vector

from app.core.base_table import BaseTable
from app.modules.document_chunks.models.chunk_jobs import ChunkJob
from app.modules.source_documents.models.source_document import SourceDocument


class DocumentChunk(BaseTable):
    __tablename__ = "document_chunks"

    source_document_id:Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("source_documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index:Mapped[int] = mapped_column(Integer, nullable=True)
    start_page:Mapped[int] = mapped_column(Integer, nullable=True)
    end_page:Mapped[int] = mapped_column(Integer, nullable=True)
    content:Mapped[str] = mapped_column(Text, nullable=True)
    embedding:Mapped[Vector] = mapped_column(Vector(1536), nullable=True)
    #metadata is reserved for sqlalchemy metadata
    meta_data:Mapped[dict] = mapped_column(JSONB,nullable=True)
    source_document = relationship(SourceDocument, back_populates="document_chunks", foreign_keys=[source_document_id])
    chunk_job_id:Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chunk_jobs.id", ondelete="CASCADE"), nullable=True)
    chunk_job = relationship(ChunkJob, back_populates="document_chunks", foreign_keys=[chunk_job_id])