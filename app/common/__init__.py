from typing import Optional, Literal
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    limit: int = Field(10, gt=0, le=10000)
    page: int = Field(1, ge=1, le=10000)
    sort_order: Literal["asc", "desc"] = "desc"
    sort_by: Optional[str] = "created_at"
    search: Optional[str] = None
