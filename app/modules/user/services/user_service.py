from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload
from sqlalchemy import select

from app.modules.auth.utils.auth_utils import get_password_hash, verify_password
from app.modules.user.models.user import User
from app.modules.user.schemas.user import UserCreate, Role as RoleEnum
from app.modules.role.models.role import Role as RoleModel
from app.modules.role.services.role_service import get_role_by_name
from fastapi import HTTPException as HttpException
from app.common import PaginationParams
from app.utils.query import paginate_query


def join_user_query():
    return (
        select(User)
        .options(
            load_only(
                User.id,
                User.name,
                User.email,
                User.role_id,
                User.is_active,
                User.last_login_at,
                User.is_verified,
                User.created_at,
                User.updated_at,
            ),
            selectinload(User.role),
        )
    )


async def get_users(params: PaginationParams, current_user: User, db: AsyncSession):
    query = join_user_query().filter(User.id != current_user.id)
    result = await paginate_query(db, query, params, [User.name, User.email])
    return result


async def get_user_by_id(db: AsyncSession, user_id: str):
    stmt = join_user_query().filter(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: UserCreate, role_name: str = "user"):
    role = await get_role_by_name(db, role_name)
    if not role:
        raise HttpException(
            status_code=400,
            detail=f"Role '{role_name}' not found. Run roles seeder first.",
        )
    db_user = User(
        email=str(user.email),
        name=user.name,
        password=get_password_hash(user.password),
        role_id=role.id,
        is_active=True,
    )
    db.add(db_user)
    await db.flush()
    return db_user


async def delete_user(db: AsyncSession, user_id: str):
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HttpException(status_code=404, detail="User not found")

    try:
        await db.delete(db_user)
        await db.commit()
    except Exception:
        await db.rollback()
        db_user.is_active = False
        await db.commit()
        raise HttpException(
            status_code=409,
            detail="Cannot delete user due to existing relationships. User has been deactivated instead.",
        )


async def update_user_by_id(db: AsyncSession, user_id: str, update_data: dict):
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HttpException(status_code=404, detail="User not found")

    if "role" in update_data and update_data["role"] is not None:
        role_enum = update_data["role"]
        role_name = role_enum.value if isinstance(role_enum, RoleEnum) else str(role_enum)
        role = await get_role_by_name(db, role_name)
        if not role:
            raise HttpException(status_code=400, detail=f"Role '{role_name}' not found")
        update_data = {**update_data, "role_id": role.id}
        del update_data["role"]

    for key, value in update_data.items():
        if hasattr(db_user, key):
            setattr(db_user, key, value)

    await db.flush()
    return db_user


async def update_user_profile(db: AsyncSession, user_id: str, update_data: dict):
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HttpException(status_code=404, detail="User not found")

    if "name" in update_data and update_data["name"] is not None:
        db_user.name = update_data["name"]

    new_password = update_data.get("password")
    old_password = update_data.get("old_password")

    if new_password is not None:
        if not old_password:
            raise HttpException(
                status_code=400,
                detail="Old password is required to set a new password",
            )
        if not db_user.password or not verify_password(old_password, db_user.password):
            raise HttpException(status_code=400, detail="Old password is incorrect")
        db_user.password = get_password_hash(new_password)

    await db.flush()
    await db.refresh(db_user)
    return {
        "id": str(db_user.id),
        "name": db_user.name,
        "email": getattr(db_user, "email", None),
        "updated_at": getattr(db_user, "updated_at", None),
    }
