"""Celery task: chunk a source document and store embeddings."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.celery_app import celery_app
from app.core.database_sync import get_sync_session
from app.modules.document_chunks.models.chunk_jobs import ChunkJob
from app.modules.document_chunks.models.document_chunk import DocumentChunk
from app.modules.document_chunks.utils.chunk_utils import (
    chunk_pages,
    build_chunk_metadata,
)
from app.modules.embedding.services.embedding_service import embed_in_batches


@celery_app.task(bind=True)
def chunk_document_task(self, job_id: str):
    """
    Load ChunkJob by id, chunk its source document's parsed_text, embed, and insert DocumentChunk rows.
    Updates job status and timestamps.
    """
    jid = uuid.UUID(job_id)
    session = get_sync_session()
    try:
        stmt = (
            select(ChunkJob)
            .options(selectinload(ChunkJob.source_document))
            .where(ChunkJob.id == jid)
        )
        job = session.execute(stmt).scalar_one_or_none()
        if not job:
            session.close()
            return {"status": "error", "detail": "Chunk job not found"}

        job.started_at = datetime.now(timezone.utc)
        job.celery_task_id = self.request.id
        session.commit()

        source_doc = job.source_document
        if not source_doc:
            job.status = "failed"
            job.error_message = "Source document not found"
            job.completed_at = datetime.now(timezone.utc)
            session.commit()
            session.close()
            return {"status": "failed", "detail": job.error_message}

        parsed = source_doc.parsed_text or {}
        pages = parsed.get("pages") or []
        if not pages:
            job.status = "failed"
            job.error_message = "Document has no parsed text; parse the document first"
            job.completed_at = datetime.now(timezone.utc)
            session.commit()
            session.close()
            return {"status": "failed", "detail": job.error_message}

        chunks = chunk_pages(pages)
        if not chunks:
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            job.error_message = None
            session.commit()
            session.close()
            return {"status": "completed", "chunks_created": 0}

        texts = [c["text"] for c in chunks]
        vectors = embed_in_batches(texts)

        rows = []
        for ch, vector in zip(chunks, vectors):
            meta = build_chunk_metadata(
                source_doc, ch["page"], ch["chunk_index"], ch["text"]
            )
            row = DocumentChunk(
                source_document_id=source_doc.id,
                chunk_job_id=job.id,
                chunk_index=ch["chunk_index"],
                start_page=ch["page"],
                end_page=ch["page"],
                content=ch["text"],
                meta_data=meta,
                embedding=vector,
            )
            rows.append(row)

        session.add_all(rows)
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = None
        session.commit()
        session.close()
        return {"status": "completed", "chunks_created": len(rows)}
    except Exception as e:
        try:
            stmt = select(ChunkJob).where(ChunkJob.id == jid)
            job = session.execute(stmt).scalar_one_or_none()
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.now(timezone.utc)
                session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
        raise
