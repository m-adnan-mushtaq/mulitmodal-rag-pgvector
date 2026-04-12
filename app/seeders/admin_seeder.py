"""Seed admin user from ADMIN_EMAIL and ADMIN_PASSWORD in .env."""
import asyncio
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.config_loader import settings
from app.modules.user.models.user import User
from app.modules.role.models.role import Role
from app.modules.auth.utils.auth_utils import get_password_hash


async def seed_admin_user():
    async with SessionLocal() as db:
        # Ensure admin role exists
        result = await db.execute(select(Role).where(Role.name == "admin"))
        admin_role = result.scalar_one_or_none()
        if not admin_role:
            print("Run roles seeder first: python -m app.seeders.roles_seeder")
            return

        # Check if admin user already exists (by email)
        email = settings.ADMIN_EMAIL
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            print(f"Admin user with email '{email}' already exists. Skipping.")
            return

        password = settings.ADMIN_PASSWORD
        admin_user = User(
            name="Admin",
            email=email,
            password=get_password_hash(password),
            role_id=admin_role.id,
            is_active=True,
            is_verified=True,
        )
        db.add(admin_user)
        await db.commit()
        print(f"Admin user created with email '{email}'.")
        print("Change the password after first login if needed.")


if __name__ == "__main__":
    asyncio.run(seed_admin_user())
