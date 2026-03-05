from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Create async engine
engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False)

# Create session maker
AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

async def get_db():
    """Dependency for getting async postgres session"""
    async with AsyncSessionLocal() as session:
        yield session
