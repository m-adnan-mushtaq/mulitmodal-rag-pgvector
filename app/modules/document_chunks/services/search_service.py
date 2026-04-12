"""Semantic search over document chunks with optional filters."""

import uuid
from typing import Any

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.document_chunks.models.document_chunk import DocumentChunk
from app.modules.embedding.services.embedding_service import embed_texts
from app.modules.source_documents.models.source_document import SourceDocument


async def semantic_search(
    db: AsyncSession,
    query: str,
    k: int = 5,
    filters: dict[str, Any] | None = None,
) -> list[dict]:
    """
    Embed query, search chunks by cosine similarity, apply optional filters.
    Returns list of dicts with chunk_id, source_document_id, page_start, page_end,
    chunk_index, distance, text, title (from meta_data), and source doc info for citations.
    """
    filters = filters or {}
    query_vec = embed_texts([query])[0]
    distance = DocumentChunk.embedding.cosine_distance(query_vec)

    stmt = (
        select(DocumentChunk, distance.label("distance"))
        .join(
            SourceDocument,
            SourceDocument.id == DocumentChunk.source_document_id,
        )
        .where(DocumentChunk.embedding.isnot(None))
    )

    if filters.get("project_id"):
        stmt = stmt.where(
            SourceDocument.project_id == uuid.UUID(filters["project_id"])
        )
    if filters.get("organization_id"):
        stmt = stmt.where(
            SourceDocument.organization_id == uuid.UUID(filters["organization_id"])
        )
    if filters.get("layer_type"):
        stmt = stmt.where(SourceDocument.layer_type == filters["layer_type"])
    if filters.get("trade"):
        stmt = stmt.where(SourceDocument.trade == filters["trade"])
    if filters.get("system"):
        stmt = stmt.where(SourceDocument.system == filters["system"])
    if filters.get("region"):
        stmt = stmt.where(SourceDocument.region == filters["region"])
    if filters.get("phase"):
        stmt = stmt.where(SourceDocument.phase == filters["phase"])

    tags_any = filters.get("tags_any")
    if tags_any:
        ors = [
            DocumentChunk.meta_data["tags"].contains([t]) for t in tags_any
        ]
        stmt = stmt.where(or_(*ors))
    tags_all = filters.get("tags_all")
    if tags_all:
        stmt = stmt.where(
            DocumentChunk.meta_data["tags"].contains(tags_all)
        )

    stmt = stmt.order_by(distance.asc()).limit(k)
    rows = (await db.execute(stmt)).all()

    results = []
    for chunk, dist in rows:
        meta = chunk.meta_data or {}
        results.append({
            "chunk_id": str(chunk.id),
            "source_document_id": str(chunk.source_document_id),
            "page_start": chunk.start_page,
            "page_end": chunk.end_page,
            "chunk_index": chunk.chunk_index,
            "distance": float(dist),
            "text": chunk.content,
            "meta_data": meta,
        })
    return results
