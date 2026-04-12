from app.db.database import get_async_session, async_session_factory

get_db = get_async_session
SessionLocal = async_session_factory
