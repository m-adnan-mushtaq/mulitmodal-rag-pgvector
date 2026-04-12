from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from .core.config_loader import settings
from fastapi.exceptions import RequestValidationError
from app.utils.exception_utils import validation_exception_handler
from app.modules.auth.routes.auth_router import auth_router
from app.modules.user.routes.user_router import user_router
from app.modules.media.routes.media_router import media_router
from app.modules.source_documents.routes.document_router import document_router
from app.modules.document_chunks.routes.chunk_router import chunk_router
from fastapi.staticfiles import StaticFiles

openapi_tags = [
    {"name": "Health Checks", "description": "Application health checks"},
    {"name": "Auth", "description": "Authentication"},
    {"name": "Users", "description": "User management"},
    {"name": "Media", "description": "File storage and uploads"},
    {"name": "Documents", "description": "Source document ingestion"},
    {"name": "Chunk Jobs", "description": "Document chunking and semantic search"},
]

app = FastAPI(title="SitenSight API", openapi_tags=openapi_tags)

app.mount('/static',StaticFiles(directory='app/static'))

if settings.BACKEND_CORS_ORIGINS:
    origins = [o.strip() for o in settings.BACKEND_CORS_ORIGINS.split(",") if o.strip()]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )

app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(media_router)
app.include_router(document_router)
app.include_router(chunk_router)


@app.get("/health", tags=["Health Checks"])
def read_root():
    return {"status": "ok"}
