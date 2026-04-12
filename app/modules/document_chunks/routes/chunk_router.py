"""Chunk jobs and semantic search routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query

from sqlalchemy.ext.asyncio import AsyncSession

from app.common import PaginationParams
from app.core.database import get_db
from app.modules.auth.middleware import authorize
from app.modules.user.models.user import User
from app.modules.document_chunks.services import (
    list_chunk_jobs,
    get_chunk_job_by_id,
    trigger_chunk_job,
    semantic_search,
)
from app.modules.document_chunks.schemas import (
    TriggerChunkJobRequest,
    SearchRequest,
)
from app.utils.common import format_response, catch_errors


chunk_router = APIRouter(prefix="/chunk-jobs", tags=["Chunk Jobs"])


@chunk_router.get("/")
@catch_errors
async def chunk_job_list(
    query: Annotated[PaginationParams, Query()],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorize()),
):
    """Paginated list of chunk jobs (no document_chunks)."""
    results = await list_chunk_jobs(db, query)
    return format_response(results["data"], status.HTTP_200_OK, results["meta"])


@chunk_router.get("/{job_id}")
@catch_errors
async def chunk_job_detail(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorize()),
):
    """Get a single chunk job by id (no document_chunks)."""
    try:
        jid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job_id",
        )
    job = await get_chunk_job_by_id(db, jid)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chunk job not found",
        )
    return format_response(job, status.HTTP_200_OK)


@chunk_router.post("/")
@catch_errors
async def chunk_job_trigger(
    payload: TriggerChunkJobRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorize()),
):
    """Create a chunk job for the given document and enqueue Celery task."""
    job = await trigger_chunk_job(db, payload.document_id, current_user.id)
    await db.commit()
    return format_response(
        job,
        status.HTTP_201_CREATED,
    )


@chunk_router.post("/search")
@catch_errors
async def chunk_search(
    payload: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorize()),
):
    """Semantic search over document chunks with optional filters. Returns sources and citations."""
    filters = None
    if payload.filters:
        filters = payload.filters.model_dump(exclude_none=True)
    results = await semantic_search(db, payload.query, k=payload.k, filters=filters)
    return format_response(
        results,
        status.HTTP_200_OK,
    )
