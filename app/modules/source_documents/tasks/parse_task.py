import uuid
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy import select
from langchain_community.document_loaders import UnstructuredURLLoader

from app.core.celery_app import celery_app
from app.core.database_sync import get_sync_session
from app.modules.media.models.media import Media
from app.modules.source_documents.models.source_document import SourceDocument
import pdfplumber
import re


# Base path for static files (same as FastAPI mount)
STATIC_BASE = Path("app/static")


def clean_text(text: str) -> str:
    """Lightweight cleaning: collapse whitespace, remove HTML-like tags, strip."""
    if not text or not isinstance(text, str):
        return ""
    # Multiple whitespace/tabs/newlines -> single space
    text = re.sub(r"\s+", " ", text)
    # Remove HTML tags (simple regex)
    text = re.sub(r"<[^>]+>", "", text)
    # Common page number patterns
    text = re.sub(r"\bPage\s+\d+\b", "", text, flags=re.IGNORECASE)
    return text.strip()

def _resolve_storage_path(storage_path: str) -> Path:
    """Resolve DB storage_path (e.g. uploads/xxx.pdf) to absolute file path."""
    return STATIC_BASE / storage_path


@celery_app.task(bind=True)
def parse_pdf_task(self, document_id: str):
    """
    Parse PDF for the given SourceDocument id: extract text per page, clean,
    store in parsed_text JSONB and set status to completed/failed.
    """
    doc_id = uuid.UUID(document_id)
    session = get_sync_session()
    try:
        # Query document + storage_path only (no relationship to User)
        stmt = (
            select(SourceDocument, Media.storage_path)
            .join(Media, SourceDocument.media_id == Media.id)
            .where(SourceDocument.id == doc_id)
        )
        row = session.execute(stmt).one_or_none()
        if not row:
            session.close()
            return {"status": "error", "detail": "Document not found"}

        doc, storage_path = row
        doc.started_at = datetime.now(timezone.utc)
        doc.celery_task_id = self.request.id
        session.commit()

        full_path = _resolve_storage_path(storage_path)
        if not full_path.exists():
            doc.status = "failed"
            doc.error_message = f"File not found: {full_path}"
            doc.completed_at = datetime.now(timezone.utc)
            session.commit()
            session.close()
            return {"status": "failed", "detail": doc.error_message}

       

        pages_data = []
        try:
            with pdfplumber.open(full_path) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    raw = page.extract_text() or ""
                    content = clean_text(raw)
                    pages_data.append({
                        "page": i,
                        "content": content,
                        "length": len(content),
                    })
        except Exception as e:
            doc.status = "failed"
            doc.error_message = str(e)
            doc.completed_at = datetime.now(timezone.utc)
            session.commit()
            session.close()
            return {"status": "failed", "detail": str(e)}

        doc.parsed_text = {
            "total_pages": len(pages_data),
            "pages": pages_data,
        }
        doc.total_pages = len(pages_data)
        doc.status = "completed"
        doc.error_message = None
        doc.completed_at = datetime.now(timezone.utc)
        session.commit()
        session.close()
        return {"status": "completed", "total_pages": len(pages_data)}
    except Exception as e:
        try:
            stmt = select(SourceDocument).where(SourceDocument.id == doc_id)
            doc = session.execute(stmt).scalar_one_or_none()
            if doc:
                doc.status = "failed"
                doc.error_message = str(e)
                doc.completed_at = datetime.now(timezone.utc)
                session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
        raise



@celery_app.task(bind=True)
def ingest_url_pdf(self, document_id: str):
    """
    Ingest a PDF from a URL using UnstructuredURLLoader and store parsed text
    in the same structure as parse_pdf_task (pages with content).
    """
    doc_id = uuid.UUID(document_id)
    session = get_sync_session()
    try:
        stmt = select(SourceDocument).where(SourceDocument.id == doc_id)
        doc = session.execute(stmt).scalar_one_or_none()
        if not doc:
            session.close()
            return {"status": "error", "detail": "Document not found"}
        if not doc.ingestion_url:
            session.close()
            return {"status": "error", "detail": "Document has no ingestion_url"}

        doc.started_at = datetime.now(timezone.utc)
        doc.celery_task_id = self.request.id
        session.commit()

        loader = UnstructuredURLLoader(
            urls=[doc.ingestion_url],
            mode="single",
        )
        docs = loader.load()
        if not docs:
            doc.status = "failed"
            doc.error_message = "No content loaded from URL"
            doc.completed_at = datetime.now(timezone.utc)
            session.commit()
            session.close()
            return {"status": "failed", "detail": doc.error_message}

        # Map to same structure as parse_pdf_task: list of { page, content, length }
        pages_data = []
        for i, lc_doc in enumerate(docs, start=1):
            raw = (lc_doc.page_content or "").strip()
            content = clean_text(raw)
            pages_data.append({
                "page": i,
                "content": content,
                "length": len(content),
            })

        doc.parsed_text = {
            "total_pages": len(pages_data),
            "pages": pages_data,
        }
        doc.total_pages = len(pages_data)
        doc.status = "completed"
        doc.error_message = None
        doc.completed_at = datetime.now(timezone.utc)
        session.commit()
        session.close()
        return {"status": "completed", "total_pages": len(pages_data)}
    except Exception as e:
        try:
            stmt = select(SourceDocument).where(SourceDocument.id == doc_id)
            doc = session.execute(stmt).scalar_one_or_none()
            if doc:
                doc.status = "failed"
                doc.error_message = str(e)
                doc.completed_at = datetime.now(timezone.utc)
                session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
        raise