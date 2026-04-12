import jwt
from datetime import datetime, timedelta, timezone
from app.core.config_loader import settings
from ..models.token import Token
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas.token import TokenTypes, ExpiryTokenMinutes
from app.modules.user.models.user import User
from fastapi import HTTPException, status
from sqlalchemy import select


# ---------------------------------------------------------------------
# Utility: always return current UTC time
# ---------------------------------------------------------------------
def utcnow() -> datetime:
    """Return the current UTC datetime (naive but treated as UTC)."""
    return datetime.utcnow()


# ---------------------------------------------------------------------
# Token generation / decoding
# ---------------------------------------------------------------------
def generate_token(
    user_id: str,
    expires: datetime,
    token_type: str,
    secret: str = settings.JWT_SECRET_KEY
) -> str:
    """Generate a signed JWT token."""
    payload = {
        "sub": str(user_id),
        "iat": utcnow(),   # ✅ always UTC
        "exp": expires,    # ✅ always UTC
        "type": token_type,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(
    token: str,
    secret: str = settings.JWT_SECRET_KEY,
    leeway: int = 5
) -> dict:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, secret, algorithms=[
                             "HS256"], leeway=leeway)
        return payload
    except jwt.ExpiredSignatureError as e:
        print("❌ Token expired:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError as e:
        print("❌ Invalid token:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


# ---------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------
async def save_token(
    db: AsyncSession,
    token: str,
    user_id: str,
    expires: datetime,
    token_type: str,
    blacklisted: bool = False
) -> Token:
    """Save a token record in the database."""
    token_obj = Token(
        token=token,
        user_id=user_id,
        type=token_type,
        expires_at=expires,  # ✅ store as UTC convention
        blacklisted=blacklisted
    )
    db.add(token_obj)
    await db.flush()
    return token_obj


# ---------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------
async def verify_token(
    db: AsyncSession,
    token: str,
    token_type: str,
    secret: str = settings.JWT_SECRET_KEY
) -> Token:
    """Verify token validity and presence in DB."""
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"], leeway=5)
    except jwt.ExpiredSignatureError as e:
        print("❌ Token expired:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.InvalidTokenError as e:
        print("❌ Invalid token:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    # ✅ compare using UTC
    result = await db.execute(
        select(Token).where(
            Token.token == token,
            Token.user_id == payload.get("sub"),
            Token.expires_at > utcnow(),
            Token.blacklisted == False
        )
    )
    token_obj = result.scalar_one_or_none()

    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Token not found"
        )

    return token_obj


# ---------------------------------------------------------------------
# Token generators
# ---------------------------------------------------------------------
def generate_auth_tokens(user: User) -> dict:
    """Generate access (and optionally refresh) tokens."""
    access_expires = utcnow() + timedelta(minutes=60)
    access_token = generate_token(user.id, access_expires, TokenTypes.ACCESS)

    return {
        "access": {
            "token": access_token,
            "expires": access_expires
        },
    }


async def generate_reset_password_token(db: AsyncSession, user: User) -> str:
    """Generate and save a reset-password token."""
    expires = utcnow() + timedelta(minutes=ExpiryTokenMinutes.RESET_PASSWORD)
    reset_token = generate_token(user.id, expires, TokenTypes.RESET_PASSWORD)

    await save_token(db, reset_token, user.id, expires, TokenTypes.RESET_PASSWORD)
    return reset_token


async def generate_email_verification_token(db: AsyncSession, user: User) -> str:
    """Generate and save an email-verification token."""
    expires = utcnow() + timedelta(minutes=ExpiryTokenMinutes.EMAIL_VERIFICATION)
    email_token = generate_token(
        user.id, expires, TokenTypes.EMAIL_VERIFICATION)

    await save_token(db, email_token, user.id, expires, TokenTypes.EMAIL_VERIFICATION)
    return email_token
