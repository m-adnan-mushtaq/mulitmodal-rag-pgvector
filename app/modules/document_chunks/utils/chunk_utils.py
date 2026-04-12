"""Chunking and metadata helpers for document chunks."""

import re
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

# Doc-level fields to snapshot into chunk meta_data (from SourceDocument)
SOURCE_DOC_METADATA_KEYS = [
    "title",
    "source_type",
    "layer_type",
    "trade",
    "division",
    "system",
    "region",
    "building_type",
    "project_type",
    "phase",
    "site_conditions",
    "experience_level",
    "constraints",
]

TAG_RULES = {
    "safety": [r"\bwarning\b", r"\bcaution\b", r"\bsafety\b", r"\bhazard\b", r"\bppe\b"],
    "installation": [r"\binstall\b", r"\bmount\b", r"\bsetup\b", r"\bwiring\b"],
    "maintenance": [r"\bmaintenance\b", r"\bservice\b", r"\bclean\b", r"\binspect\b"],
    "troubleshooting": [r"\btroubleshoot\b", r"\bfault\b", r"\berror\b", r"\bdiagnos"],
    "specifications": [r"\bspec\b", r"\bvoltage\b", r"\bdimension\b", r"\bpressure\b"],
}

SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
)


def _serialize_value(v: Any) -> Any:
    """Serialize value for JSONB (e.g. UUID -> str)."""
    if hasattr(v, "hex"):
        return str(v)
    return v


def tag_text(text: str) -> list[str]:
    """Return rule-based tags for the given text."""
    if not text:
        return []
    t = text.lower()
    tags = []
    for tag, pats in TAG_RULES.items():
        if any(re.search(p, t) for p in pats):
            tags.append(tag)
    return tags


def build_chunk_metadata(source_doc, page: int, chunk_index: int, text: str) -> dict:
    """Build chunk meta_data from source doc snapshot + citation + tags."""
    meta = {
        "page_start": page,
        "page_end": page,
        "chunk_index": chunk_index,
        "source_document_id": str(source_doc.id),
    }
    for key in SOURCE_DOC_METADATA_KEYS:
        if hasattr(source_doc, key):
            meta[key] = _serialize_value(getattr(source_doc, key))
    meta["tags"] = tag_text(text)
    return meta


def chunk_pages(parsed_pages: list[dict]) -> list[dict]:
    """
    Split each page's content into equal-sized chunks.
    parsed_pages: list of {"page": int, "content": str, ...} (e.g. from parsed_text["pages"]).
    Returns list of {"page": int, "chunk_index": int, "text": str}.
    """
    chunks = []
    global_index = 0
    for page_obj in sorted(parsed_pages, key=lambda x: x.get("page", 0)):
        page_number = int(page_obj.get("page", 0))
        text = (page_obj.get("content") or "").strip()
        if not text:
            continue
        parts = SPLITTER.split_text(text)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            chunks.append({
                "page": page_number,
                "chunk_index": global_index,
                "text": part,
            })
            global_index += 1
    return chunks
