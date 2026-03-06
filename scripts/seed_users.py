import asyncio
import os
import sys

# Add the project root directory to the python path so 'app' can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.security import get_password_hash
from app.db.postgres import AsyncSessionLocal
from app.enums.role import UserRole
from app.models.user import User


async def seed_users():
    async with AsyncSessionLocal() as session:
        # Check if already exists
        from app.repositories.sqlalchemy_user import SqlAlchemyUserRepository

        repo = SqlAlchemyUserRepository(session)
        management = await repo.get_by_email("management@test.com")
        if not management:
            print("Creating Management User...")
            new_user = User(
                email="management@test.com",
                hashed_password=get_password_hash("123456789"),
                role=UserRole.MANAGEMENT,
            )
            session.add(new_user)
            await session.commit()
            print("Management user created successfully.")
        else:
            print("Management user already exists.")

        supervisor = await repo.get_by_email("supervisor@test.com")
        if not supervisor:
            print("Creating Supervisor User...")
            new_user = User(
                email="supervisor@test.com",
                hashed_password=get_password_hash("123456789"),
                role=UserRole.SUPERVISOR,
            )
            session.add(new_user)
            await session.commit()
            print("Supervisor user created successfully.")
        else:
            print("Supervisor user already exists.")

        operator = await repo.get_by_email("operator@test.com")
        if not operator:
            print("Creating Operator User...")
            new_user = User(
                email="operator@test.com",
                hashed_password=get_password_hash("123456789"),
                role=UserRole.OPERATOR,
            )
            session.add(new_user)
            await session.commit()
            print("Operator user created successfully.")
        else:
            print("Operator user already exists.")


if __name__ == "__main__":
    asyncio.run(seed_users())
