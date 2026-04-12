from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field
import uuid
import datetime


class SourceType(str, Enum):
    PDF = "pdf"
    SPEC = "spec"
    MANUAL = "manual"
    CODE = "code"


class LayerType(str, Enum):
    GLOBAL = "GLOBAL"
    COMPANY = "COMPANY"
    PROJECT = "PROJECT"


class DocumentUploadForm(BaseModel):
    """Form fields for POST /documents (multipart). File handled separately."""
    title: str = Field(..., min_length=1)
    source_type: SourceType = SourceType.PDF
    layer_type: LayerType
    organization_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    trade: Optional[str] = None
    division: Optional[str] = None
    system: Optional[str] = None
    region: Optional[str] = None
    building_type: Optional[str] = None
    project_type: Optional[str] = None
    phase: Optional[str] = None
    site_conditions: Optional[str] = None
    experience_level: Optional[str] = None
    constraints: Optional[str] = None
    parent_document_id: Optional[uuid.UUID] = None
    ingestion_type: Optional[str] = None
    ingestion_url: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    document_id: uuid.UUID
    status: str = "processing"


class DocumentOut(BaseModel):
    id: uuid.UUID
    media_id: Optional[uuid.UUID] = None
    ingestion_type: Optional[str] = None
    ingestion_url: Optional[str] = None
    title: str
    source_type: str
    layer_type: str
    organization_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    trade: Optional[str] = None
    division: Optional[str] = None
    system: Optional[str] = None
    region: Optional[str] = None
    building_type: Optional[str] = None
    project_type: Optional[str] = None
    phase: Optional[str] = None
    site_conditions: Optional[str] = None
    experience_level: Optional[str] = None
    constraints: Optional[str] = None
    total_pages: Optional[int] = None
    parsed_text: Optional[dict[str, Any]] = None
    status: str
    celery_task_id: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None
    root_document_id: Optional[uuid.UUID] = None
    version: int
    is_active: bool
    parent_document_id: Optional[uuid.UUID] = None
    created_by: uuid.UUID
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


class DocumentDetailOut(DocumentOut):
    """Optional: include nested media when needed."""
    pass
