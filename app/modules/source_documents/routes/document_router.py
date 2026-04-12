import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, status, Query, UploadFile

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.middleware import authorize
from app.modules.user.models.user import User
from app.modules.source_documents.services.document_service import (
    create_document,
    trigger_parse_task,
    trigger_ingest_url_task,
    list_active_documents,
    get_document_history,
    get_document_by_id,
    delete_document,
)
from app.modules.source_documents.schemas.document import (
    DocumentUploadForm,
    DocumentUploadResponse,
    SourceType,
    LayerType,
)
from app.utils.common import format_response, catch_errors, parse_uuid
from app.common import PaginationParams


document_router = APIRouter(prefix="/documents", tags=["Documents"])





@document_router.post("/")
@catch_errors
async def document_upload(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorize()),
    file: Optional[UploadFile] = File(None, description="PDF file (optional if ingestion_url provided)"),
    ingestion_url: Optional[str] = Form(None, description="URL of PDF to ingest (optional if file uploaded)"),
    title: str = Form(..., min_length=1),
    source_type: str = Form("pdf"),
    layer_type: str = Form(...),
    organization_id: Optional[str] = Form(None),
    project_id: Optional[str] = Form(None),
    trade: Optional[str] = Form(None),
    division: Optional[str] = Form(None),
    system: Optional[str] = Form(None),
    region: Optional[str] = Form(None),
    building_type: Optional[str] = Form(None),
    project_type: Optional[str] = Form(None),
    phase: Optional[str] = Form(None),
    site_conditions: Optional[str] = Form(None),
    experience_level: Optional[str] = Form(None),
    constraints: Optional[str] = Form(None),
    parent_document_id: Optional[str] = Form(None),
):
    has_file = file is not None and (file.filename or "").strip() != ""
    if has_file and ingestion_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either file or ingestion_url, not both.",
        )
    if not has_file and not (ingestion_url and ingestion_url.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either a PDF file or ingestion_url.",
        )
    form = DocumentUploadForm(
        title=title,
        source_type=SourceType(source_type),
        layer_type=LayerType(layer_type),
        organization_id=parse_uuid(organization_id),
        project_id=parse_uuid(project_id),
        trade=trade or None,
        division=division or None,
        system=system or None,
        region=region or None,
        building_type=building_type or None,
        project_type=project_type or None,
        phase=phase or None,
        site_conditions=site_conditions or None,
        experience_level=experience_level or None,
        constraints=constraints or None,
        parent_document_id=parse_uuid(parent_document_id),
        ingestion_type="url" if ingestion_url and ingestion_url.strip() else "file",
        ingestion_url=ingestion_url.strip() if ingestion_url and ingestion_url.strip() else None,
    )
    doc = await create_document(db, current_user.id, file if has_file else None, form)
    if form.ingestion_type == "url":
        task_id = await trigger_ingest_url_task(doc.id)
    else:
        task_id = await trigger_parse_task(doc.id)
    doc.celery_task_id = task_id
    await db.flush()
    return format_response(
        DocumentUploadResponse(document_id=doc.id, status="processing"),
        status.HTTP_201_CREATED,
    )


@document_router.get("/")
@catch_errors
async def document_list(
    query: Annotated[PaginationParams, Query()],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorize()),
):
    results = await list_active_documents(db, query)
    return format_response(results["data"], status.HTTP_200_OK, results["meta"])


@document_router.get("/history/{root_document_id}")
@catch_errors
async def document_history(
    root_document_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(authorize()),
):
    try:
        root_id = uuid.UUID(root_document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid root_document_id",
        )
    history = await get_document_history(db, root_id)
    return format_response(history, status.HTTP_200_OK)


@document_router.get("/{document_id}")
@catch_errors
async def document_detail(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(authorize()),
):
    try:
        doc_id = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document_id",
        )
    doc = await get_document_by_id(db, doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return format_response(doc, status.HTTP_200_OK)


@document_router.delete("/{document_id}")
@catch_errors
async def document_delete(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorize()),
):
    try:
        doc_id = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document_id",
        )
    doc = await get_document_by_id(db, doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    if doc.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to delete this document",
        )
    await delete_document(db, doc_id)
    return format_response(None, status.HTTP_204_NO_CONTENT)
