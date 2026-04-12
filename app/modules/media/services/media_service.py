from sqlalchemy import select
from sqlalchemy.orm import load_only, selectinload

from app.common import PaginationParams
from app.utils.query import paginate_query

from app.modules.media.models.media import Media
from app.modules.user.models.user import User
from fastapi import HTTPException
from app.utils.file_utils import delete_file

def join_media_query():
    return (
        select(Media)
        .options(
            load_only(
                Media.id,
                Media.file_name,
                Media.file_size,
                Media.mime_type,
                Media.storage_path,
                Media.uploaded_by,
                Media.created_at,
                Media.updated_at,
            ),
            selectinload(Media.uploader).load_only(User.id, User.name, User.email),
        )
    )


async def get_media_list(
    db,
    params: PaginationParams,
    uploaded_by=None,
):
    query = join_media_query()
    if uploaded_by is not None:
        query = query.filter(Media.uploaded_by == uploaded_by)
    result = await paginate_query(
        db, query, params, [Media.file_name, Media.mime_type]
    )
    return result


async def get_media_by_id(db, media_id):
    stmt = join_media_query().filter(Media.id == media_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def delete_media(db, media_id):   
    media = await get_media_by_id(db, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    if media.storage_path:
        delete_file(media.storage_path)

    await db.delete(media)
    await db.flush()
    return media
