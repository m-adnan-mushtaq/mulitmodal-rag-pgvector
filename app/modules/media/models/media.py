import uuid
from sqlalchemy import String, Integer, BigInteger, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_table import BaseTable
from app.modules.user.models.user import User


class Media(BaseTable):
    __tablename__ = "media"

    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )

    # Relationships
    uploader = relationship(User, back_populates="media", foreign_keys=[uploaded_by])
    source_documents = relationship(
        "SourceDocument",
        back_populates="media",
        foreign_keys="SourceDocument.media_id",
    )
