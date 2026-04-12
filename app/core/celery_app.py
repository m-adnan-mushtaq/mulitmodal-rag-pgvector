from celery import Celery
from app.core.config_loader import settings

celery_app = Celery(
    "worker",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    include=[
        "app.modules.source_documents.tasks.parse_task",
        "app.modules.document_chunks.tasks.chunk_task",
    ],
)

import app.modules.source_documents.tasks.parse_task
import app.modules.document_chunks.tasks.chunk_task