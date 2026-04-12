from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.role.models.role import Role as RoleModel


async def get_role_by_name(db: AsyncSession, name: str):
    result = await db.execute(select(RoleModel).where(RoleModel.name == name))
    return result.scalar_one_or_none()
