"""Chunk job service: list, get by id, trigger chunking (Celery)."""

import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import load_only, selectinload

from app.common import PaginationParams
from app.utils.query import paginate_query
from app.modules.document_chunks.models.chunk_jobs import ChunkJob
from app.modules.document_chunks.tasks.chunk_task import chunk_document_task
from app.modules.source_documents.models.source_document import SourceDocument
from app.modules.source_documents.services.document_service import get_document_by_id
from app.modules.user.models.user import User
from app.modules.media.models.media import Media


def join_chunk_job_query():
    """Base query for ChunkJob without loading document_chunks."""
    return (
        select(ChunkJob)
        .options(
            load_only(
                ChunkJob.id,
                ChunkJob.source_document_id,
                ChunkJob.status,
                ChunkJob.celery_task_id,
                ChunkJob.error_message,
                ChunkJob.started_at,
                ChunkJob.completed_at,
                ChunkJob.created_by_id,
                ChunkJob.created_at,
                ChunkJob.updated_at,
            ),
            selectinload(ChunkJob.source_document).load_only(
                SourceDocument.id,
                SourceDocument.title,
                SourceDocument.status,
                SourceDocument.project_id,
                SourceDocument.organization_id,
                SourceDocument.layer_type,
                SourceDocument.trade,
                SourceDocument.system,
                SourceDocument.region,
                SourceDocument.phase,
                SourceDocument.site_conditions,
                SourceDocument.experience_level,
                SourceDocument.constraints,
            ),
            selectinload(ChunkJob.source_document)
                .selectinload(SourceDocument.media)
                .load_only(
                    Media.id,
                    Media.file_name,
                    Media.file_size,
                    Media.mime_type,
                    Media.storage_path,
                ),
            selectinload(ChunkJob.created_by).load_only(User.id, User.name, User.email),
        )
    )


async def list_chunk_jobs(db, params: PaginationParams):
    """Paginated list of chunk jobs (no document_chunks)."""
    query = join_chunk_job_query()
    return await paginate_query(
        db,
        query,
        params,
        searchable_columns=[ChunkJob.status],
    )


async def get_chunk_job_by_id(db, job_id: uuid.UUID):
    """Get a single chunk job by id (no document_chunks)."""
    stmt = join_chunk_job_query().where(ChunkJob.id == job_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def trigger_chunk_job(db, document_id: uuid.UUID, user_id: uuid.UUID):
    """
    Create a ChunkJob for the given document and current user, enqueue Celery task, return job.
    """
    doc = await get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.parsed_text or not (doc.parsed_text.get("pages")):
        raise HTTPException(
            status_code=400,
            detail="Document has no parsed text; parse the document first",
        )

    job = ChunkJob(
        source_document_id=document_id,
        created_by_id=user_id,
        status="processing",
    )
    db.add(job)
    await db.flush()

    chunk_document_task.delay(str(job.id))
    return job
