
from jwt.exceptions import InvalidTokenError
from sqlalchemy import delete
from ..utils.auth_utils import verify_password, get_password_hash
from app.core.config_loader import settings
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession as Session
from fastapi import Depends, HTTPException, status
import jwt
from app.core.database import get_db
from app.modules.jwt_token.models.token import Token
from app.modules.jwt_token.services import token_service
from app.modules.jwt_token.schemas.token import TokenTypes
from app.modules.user.models.user import User
from app.modules.user.schemas.user import UserCreate, UserOut
from app.modules.user.services import user_service
from app.modules.jwt_token.services import token_service
from app.shared import email_service
from datetime import datetime
from fastapi import BackgroundTasks

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"

security = HTTPBearer()


async def register_user(db: Session, user: UserCreate, background_tasks: BackgroundTasks):
    try:
        db_user = await user_service.get_user_by_email(db, email=user.email)
        if db_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Email already registered")
        new_user = await user_service.create_user(db, user)
        verify_email_token = await token_service.generate_email_verification_token(
            db, new_user)
        background_tasks.add_task(email_service.send_verification_email,
                                  new_user.email, verify_email_token)
        await db.commit()
        new_user.password = None
        return new_user
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise


async def authenticate_user(email: str, password: str, db: Session):

    user = await user_service.get_user_by_email(db, email)
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Your account has been deactivated by admin, please contact support.")
    if not user.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Email not verified. Please check your inbox or reset your password to receive a new verification email.")
    tokens = token_service.generate_auth_tokens(user)

    # update user last login
    await user_service.update_user_by_id(db, user.id, {"last_login_at": datetime.now()})
   
    user_data = user.__dict__.copy()
    user_data.pop("_sa_instance_state", None)
    user_data["password"] = None
    return {
        "user": user_data,
        "tokens": tokens
    }


async def reset_password(db: Session, reset_password_token: str, new_password: str):
    """
    Reset a user's password using a valid token.
    """
    try:
        token_doc = await token_service.verify_token(
            db, reset_password_token, TokenTypes.RESET_PASSWORD)
        user = await user_service.get_user_by_id(db, token_doc.user_id)

        if not user:
            raise ValueError("User not found")

        hashed_password = get_password_hash(new_password)
        await user_service.update_user_by_id(
            db, user.id, {"password": hashed_password, "is_verified": True})

        await db.execute(delete(Token).where(Token.user_id == user.id, Token.type == TokenTypes.RESET_PASSWORD))

        await db.commit()
        user.password = None

    except Exception:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Password reset failed")


async def forgot_password(db: Session, email: str, background_tasks: BackgroundTasks):
    """
    Generate a reset password token and send it to the user's email.
    """

    try:
        user = await user_service.get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No user found with this email")
        token = await token_service.generate_reset_password_token(db, user)

        # send email
        background_tasks.add_task(
            email_service.send_reset_password_email, user.email, token)
        await db.commit()
        return {"message": "Password reset email sent"}

    except:
        await db.rollback()
        raise


# ----------------------------------------------------
# Verify email
# ----------------------------------------------------
async def verify_email(db: Session, verify_email_token: str):
    """
    Verify a user's email address using a valid token.
    """
    try:
        token_doc = await token_service.verify_token(
            db, verify_email_token, TokenTypes.EMAIL_VERIFICATION)
        user = await user_service.get_user_by_id(db, token_doc.user_id)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="User not found")

        # Remove all verify-email tokens

        await db.execute(delete(Token).where(Token.user_id == user.id, Token.type == TokenTypes.EMAIL_VERIFICATION))

        # Update user record
        await user_service.update_user_by_id(
            db, user.id, {"is_verified": True})
        await db.commit()

        return {"message": "Email verified successfully"}

    except Exception as e:
        print(e)
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Email verification failed")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = token_service.decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        user = await user_service.get_user_by_id(db, user_id=user_id)
        if user is None:
            raise credentials_exception

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Your account has been deactivated by admin, please contact support.")
        if not user.is_verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Email not verified. Please check your inbox or reset your password to receive a new verification email.")

        return user
    except (jwt.PyJWTError, InvalidTokenError):
        raise credentials_exception


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user
