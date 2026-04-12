from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..services import auth_service
from app.core.database import get_db
from app.utils.common import catch_errors, format_response
from ..models import auth
from fastapi import status, BackgroundTasks
from app.modules.user.schemas import user

auth_router = APIRouter(
    prefix='/auth',
    tags=['Auth'],
)


@auth_router.post('/login')
@catch_errors
async def login(
    payload: auth.LoginReq,
    db: AsyncSession = Depends(get_db)
):
    result = await auth_service.authenticate_user(
        payload.email, payload.password, db=db)
    return format_response(result, status.HTTP_200_OK)


@auth_router.post('/register')
@catch_errors
async def register(
    payload: user.UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    result = await auth_service.register_user(db, payload, background_tasks)
    return format_response(result, status.HTTP_201_CREATED)


@auth_router.post('/forgot-password')
@catch_errors
async def forgot_password(
    payload: auth.ForgotPasswordReq,
        background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    result = await auth_service.forgot_password(db, payload.email, background_tasks)
    return format_response(result, status.HTTP_200_OK)


@auth_router.post('/reset-password')
@catch_errors
async def reset_password(
    payload: auth.ResetPasswordReq,
    db: AsyncSession = Depends(get_db)
):
    result = await auth_service.reset_password(db, payload.token, payload.password)
    return format_response(result, status.HTTP_200_OK)


@auth_router.post('/verify-email')
@catch_errors
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    result = await auth_service.verify_email(db, token)
    return format_response(result, status.HTTP_200_OK)
