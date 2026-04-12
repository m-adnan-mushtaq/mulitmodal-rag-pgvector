"""Seed roles: Admin, SME, User."""
import asyncio
from sqlalchemy import select

from app.core.database import SessionLocal
from app.modules.user.models.user import User  # noqa: F401 - register so Role.relationship("User") resolves
from app.modules.role.models.role import Role


ROLES = [
    ("admin", "Administrator with full access"),
    ("sme", "Subject matter expert"),
    ("user", "Standard user"),
]


async def seed_roles():
    async with SessionLocal() as db:
        for name, description in ROLES:
            result = await db.execute(select(Role).where(Role.name == name))
            if result.scalar_one_or_none():
                print(f"Role '{name}' already exists. Skipping.")
                continue
            role = Role(name=name, description=description, is_active=True)
            db.add(role)
            print(f"Created role: {name}")
        await db.commit()
    print("Roles seeding done.")


if __name__ == "__main__":
    asyncio.run(seed_roles())
