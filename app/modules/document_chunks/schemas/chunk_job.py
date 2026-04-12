"""Schemas for chunk jobs."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TriggerChunkJobRequest(BaseModel):
    """Body for POST /chunk-jobs: start chunking a document."""

    document_id: uuid.UUID = Field(..., description="Source document to chunk")


class ChunkJobSourceDocumentRef(BaseModel):
    """Minimal source document ref in chunk job response."""

    id: uuid.UUID
    title: Optional[str] = None
    status: Optional[str] = None

    model_config = {"from_attributes": True}


class ChunkJobCreatedByRef(BaseModel):
    """Who started the job."""

    id: uuid.UUID
    name: Optional[str] = None
    email: Optional[str] = None

    model_config = {"from_attributes": True}


class ChunkJobResponse(BaseModel):
    """Single chunk job (no document_chunks list)."""

    id: uuid.UUID
    source_document_id: Optional[uuid.UUID] = None
    status: str
    celery_task_id: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by_id: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source_document: Optional[ChunkJobSourceDocumentRef] = None
    created_by: Optional[ChunkJobCreatedByRef] = None

    model_config = {"from_attributes": True}
