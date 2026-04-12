from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.base_table import BaseTable
from app.modules.jwt_token.models.token import Token
from app.modules.source_documents.models.source_document import SourceDocument
from app.modules.role.models.role import Role


class User(BaseTable):
    __tablename__ = 'users'

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    last_login_at: Mapped[DateTime] = mapped_column(
        DateTime, default=None, nullable=True)

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False
    )

    # Relationships
    tokens = relationship(Token, back_populates="user", passive_deletes=True)
    role = relationship(Role, back_populates="users")
    media = relationship(
        "Media",
        back_populates="uploader",
        foreign_keys="Media.uploaded_by",
    )
    source_documents = relationship(
        SourceDocument,
        back_populates="creator",
        foreign_keys="SourceDocument.created_by",
    )
    chunk_jobs = relationship(
        "ChunkJob",
        back_populates="created_by",
        foreign_keys="ChunkJob.created_by_id",
    )
