import uuid
from pathlib import Path

from typing import Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import load_only, selectinload

from app.common import PaginationParams
from app.utils.query import paginate_query

from app.modules.media.models.media import Media
from app.modules.user.models.user import User
from app.modules.source_documents.models.source_document import SourceDocument
from app.modules.source_documents.schemas.document import (
    DocumentUploadForm,
    LayerType,
)
from sqlalchemy import update
from app.modules.source_documents.tasks.parse_task import parse_pdf_task, ingest_url_pdf
from app.modules.media.services import media_service

# Storage directory relative to project root; mount at app/static
UPLOAD_DIR = Path("app/static/uploads")


def _ensure_upload_dir():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _save_file(file: UploadFile, prefix: str) -> tuple[str, int]:
    """Save file to disk. Returns (storage_path, file_size). storage_path is relative for DB."""
    _ensure_upload_dir()
    ext = Path(file.filename or "").suffix or ".pdf"
    unique_name = f"{prefix}_{uuid.uuid4().hex}{ext}"
    path = UPLOAD_DIR / unique_name
    size = 0
    with path.open("wb") as f:
        while chunk := file.file.read(64 * 1024):
            size += len(chunk)
            f.write(chunk)
    return f"uploads/{unique_name}", size


def _validate_upload_form(form: DocumentUploadForm):
    if form.layer_type == LayerType.COMPANY and not form.organization_id:
        raise HTTPException(
            status_code=400,
            detail="organization_id is required when layer_type is COMPANY",
        )
    if form.layer_type == LayerType.PROJECT:
        if not form.organization_id:
            raise HTTPException(
                status_code=400,
                detail="organization_id is required when layer_type is PROJECT",
            )
        if not form.project_id:
            raise HTTPException(
                status_code=400,
                detail="project_id is required when layer_type is PROJECT",
            )


def join_document_query():
    return (
        select(SourceDocument)
        .options(
            load_only(
                SourceDocument.id,
                SourceDocument.media_id,
                SourceDocument.ingestion_type,
                SourceDocument.ingestion_url,
                SourceDocument.title,
                SourceDocument.source_type,
                SourceDocument.layer_type,
                SourceDocument.organization_id,
                SourceDocument.project_id,
                SourceDocument.trade,
                SourceDocument.division,
                SourceDocument.system,
                SourceDocument.region,
                SourceDocument.building_type,
                SourceDocument.project_type,
                SourceDocument.phase,
                SourceDocument.site_conditions,
                SourceDocument.experience_level,
                SourceDocument.constraints,
                SourceDocument.total_pages,
                SourceDocument.parsed_text,
                SourceDocument.status,
                SourceDocument.celery_task_id,
                SourceDocument.error_message,
                SourceDocument.started_at,
                SourceDocument.completed_at,
                SourceDocument.root_document_id,
                SourceDocument.version,
                SourceDocument.is_active,
                SourceDocument.parent_document_id,
                SourceDocument.created_by,
                SourceDocument.created_at,
                SourceDocument.updated_at,
            ),
            selectinload(SourceDocument.media).load_only(
                Media.id, Media.file_name, Media.file_size, Media.mime_type, Media.storage_path
            ),
            selectinload(SourceDocument.creator).load_only(User.id, User.name, User.email),
        )
    )


async def create_document(
    db, user_id: uuid.UUID, file: Optional[UploadFile], form: DocumentUploadForm
):
    _validate_upload_form(form)

    media_id: Optional[uuid.UUID] = None
    if file is not None:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        prefix = uuid.uuid4().hex[:12]
        storage_path, file_size = _save_file(file, prefix)
        media = Media(
            file_name=file.filename or "document.pdf",
            file_size=file_size,
            mime_type=file.content_type or "application/pdf",
            storage_path=storage_path,
            uploaded_by=user_id,
        )
        db.add(media)
        await db.flush()
        media_id = media.id
    else:
        if not form.ingestion_url or form.ingestion_type != "url":
            raise HTTPException(
                status_code=400,
                detail="ingestion_url is required when no file is uploaded.",
            )

    root_id: Optional[uuid.UUID] = None
    version = 1
    parent_id: Optional[uuid.UUID] = form.parent_document_id

    if parent_id:
        parent_stmt = select(SourceDocument).filter(SourceDocument.id == parent_id)
        parent_row = await db.execute(parent_stmt)
        parent_doc = parent_row.scalar_one_or_none()
        if not parent_doc:
            raise HTTPException(status_code=404, detail="Parent document not found")
        root_id = parent_doc.root_document_id or parent_doc.id
        version = parent_doc.version + 1

        await db.execute(
            update(SourceDocument)
            .where(SourceDocument.root_document_id == root_id)
            .values(is_active=False)
        )

    doc = SourceDocument(
        media_id=media_id,
        ingestion_type=form.ingestion_type or ("url" if form.ingestion_url else "file"),
        ingestion_url=form.ingestion_url,
        title=form.title,
        source_type=form.source_type.value,
        layer_type=form.layer_type.value,
        organization_id=form.organization_id,
        project_id=form.project_id,
        trade=form.trade,
        division=form.division,
        system=form.system,
        region=form.region,
        building_type=form.building_type,
        project_type=form.project_type,
        phase=form.phase,
        site_conditions=form.site_conditions,
        experience_level=form.experience_level,
        constraints=form.constraints,
        status="processing",
        root_document_id=root_id,
        version=version,
        is_active=True,
        parent_document_id=parent_id,
        created_by=user_id,
    )
    db.add(doc)
    await db.flush()
    if not root_id:
        doc.root_document_id = doc.id
        await db.flush()

    return doc


async def trigger_parse_task(document_id: uuid.UUID) -> str | None:
    """Trigger Celery task to parse PDF. Returns task_id."""
    
    result = parse_pdf_task.delay(str(document_id))
    return result.id if result else None

async def trigger_ingest_url_task(document_id: uuid.UUID) -> str | None:
    """Trigger Celery task to ingest PDF from URL. Returns task_id."""
    result = ingest_url_pdf.delay(str(document_id))
    return result.id if result else None

async def list_active_documents(db, params: PaginationParams):
    query = join_document_query().filter(
        SourceDocument.is_active == True
    )
    return await paginate_query(
        db, query, params,
        [SourceDocument.title, SourceDocument.source_type],
    )


async def get_document_history(db, root_document_id: uuid.UUID):
    query = (
        join_document_query()
        .filter(SourceDocument.root_document_id == root_document_id)
        .order_by(SourceDocument.version.desc())
    )
    result = await db.execute(query)
    return result.scalars().unique().all()


async def get_document_by_id(db, document_id: uuid.UUID):
    stmt = join_document_query().filter(SourceDocument.id == document_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def delete_document(db, document_id: uuid.UUID):
    doc = await get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete related media if any
    if hasattr(doc, "media") and doc.media:
        await media_service.delete_media(db, doc.media.id)
    
    await db.delete(doc)
    await db.flush()
    return doc
