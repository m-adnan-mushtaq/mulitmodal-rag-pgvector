from typing import Optional
from pydantic import BaseModel
import uuid
import datetime


class MediaOut(BaseModel):
    id: uuid.UUID
    file_name: str
    file_size: int
    mime_type: str
    storage_path: str
    uploaded_by: uuid.UUID
    created_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True
