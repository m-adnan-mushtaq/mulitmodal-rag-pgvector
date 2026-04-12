from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.base_table import BaseTable


class Token(BaseTable):
    __tablename__ = 'tokens'

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('users.id', ondelete="CASCADE"), nullable=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    token: Mapped[str] = mapped_column(
        String(512), unique=True, nullable=False)
    blacklisted: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)

    # user
    user = relationship("User", back_populates="tokens")
