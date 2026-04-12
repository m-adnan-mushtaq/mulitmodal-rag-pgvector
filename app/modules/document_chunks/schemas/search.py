"""Schemas for semantic search over document chunks."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    """Optional filters for semantic search."""

    project_id: Optional[str] = None
    organization_id: Optional[str] = None
    layer_type: Optional[str] = None
    trade: Optional[str] = None
    system: Optional[str] = None
    region: Optional[str] = None
    phase: Optional[str] = None
    tags_any: Optional[list[str]] = None  # match any of these tags
    tags_all: Optional[list[str]] = None  # match all of these tags


class SearchRequest(BaseModel):
    """Body for POST /chunk-jobs/search."""

    query: str = Field(..., min_length=1, description="Search query text")
    k: int = Field(5, ge=1, le=50, description="Max number of results")
    filters: Optional[SearchFilters] = None

