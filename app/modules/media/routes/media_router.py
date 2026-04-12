from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.middleware import authorize
from app.modules.user.models.user import User
from app.modules.media.services.media_service import (
    get_media_list,
    get_media_by_id,
    delete_media,
)
from app.utils.common import format_response, catch_errors
from app.common import PaginationParams

media_router = APIRouter(prefix="/media", tags=["Media"])


@media_router.get("/")
@catch_errors
async def media_list(
    query: Annotated[PaginationParams, Query()],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorize()),
):
    # List media uploaded by the current user
    results = await get_media_list(db, query, uploaded_by=current_user.id)
    return format_response(results["data"], status.HTTP_200_OK, results["meta"])


@media_router.get("/{media_id}")
@catch_errors
async def media_detail(
    media_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorize()),
):
    media = await get_media_by_id(db, media_id)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found",
        )
    return format_response(media, status.HTTP_200_OK)


@media_router.delete("/{media_id}")
@catch_errors
async def media_delete(
    media_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorize()),
):
    media = await get_media_by_id(db, media_id)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found",
        )
    if media.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to delete this media",
        )
    await delete_media(db, media_id)
    return format_response(None, status.HTTP_204_NO_CONTENT)
