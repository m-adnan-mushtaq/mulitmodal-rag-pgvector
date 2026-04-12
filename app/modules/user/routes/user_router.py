from fastapi import APIRouter, Depends, HTTPException, status, Query

from sqlalchemy.ext.asyncio import AsyncSession as Session

from app.modules.auth.middleware import authorize
from app.core.database import get_db
from ..models.user import User
from ..schemas.user import Role, UpdateProfile, UpdateUser
from ..services.user_service import get_users, delete_user, get_user_by_id, update_user_profile, update_user_by_id
from app.utils.common import format_response, catch_errors
from typing import Annotated
from app.common import PaginationParams

user_router = APIRouter(
    prefix='/users',
    tags=['Users']
)


@user_router.get('/')
@catch_errors
async def user_list(query: Annotated[PaginationParams, Query()], db: Session = Depends(get_db), current_user: User = Depends(authorize(Role.ADMIN.value))):
    results = await get_users(query, current_user, db)
    return format_response(results, status.HTTP_200_OK)


@user_router.get('/me')
@catch_errors
async def get_me(current_user: User = Depends(authorize())):
    return format_response(current_user, status.HTTP_200_OK)


@user_router.get('/{user_id}')
@catch_errors
async def user_detail(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(authorize(Role.ADMIN.value))):
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db_user.password = None  # Remove password before returning
    return format_response(db_user, status.HTTP_200_OK)


@user_router.patch('/profile')
@catch_errors
async def update_profile(payload: UpdateProfile, db: Session = Depends(get_db), current_user: User = Depends(authorize())):
    result = await update_user_profile(
        db, user_id=current_user.id, update_data=payload.model_dump())

    return format_response(result, status.HTTP_200_OK)


@user_router.patch('/{user_id}')
@catch_errors
async def update_user(user_id: str, payload: UpdateUser, db: Session = Depends(get_db), current_user: User = Depends(authorize(Role.ADMIN.value))):
    result = await update_user_by_id(
        db, user_id=user_id, update_data=payload.model_dump(exclude_unset=True))
    await db.commit()
    result.password = None  # Remove password before returning
    return format_response(result, status.HTTP_200_OK)


@user_router.delete('/{user_id}')
@catch_errors
async def user_delete(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(authorize(Role.ADMIN.value))):
    result = await delete_user(db, user_id)
    return format_response(result, status.HTTP_200_OK)
