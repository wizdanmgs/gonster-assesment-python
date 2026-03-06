import asyncio
import os
import sys

# Add the project root directory to the python path so 'app' can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.security import get_password_hash
from app.db.postgres import AsyncSessionLocal
from app.models.user import User, UserRole


async def seed_management_user():
    async with AsyncSessionLocal() as session:
        # Check if already exists
        from app.repositories.sqlalchemy_user import SqlAlchemyUserRepository

        repo = SqlAlchemyUserRepository(session)
        user = await repo.get_by_email("admin@test.com")
        if not user:
            print("Creating Admin User...")
            new_user = User(
                email="admin@test.com",
                hashed_password=get_password_hash("123456789"),
                role=UserRole.Management,
            )
            session.add(new_user)
            await session.commit()
            print("Admin user created successfully.")
        else:
            print("Admin user already exists.")


if __name__ == "__main__":
    asyncio.run(seed_management_user())
