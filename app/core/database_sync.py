"""Sync SQLAlchemy engine/session for Celery workers (non-async)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config_loader import settings

_engine = create_engine(
    settings.database_url_sync,
    pool_pre_ping=True,
)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def get_sync_session() -> Session:
    return SyncSessionLocal()
