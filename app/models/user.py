import uuid
from sqlalchemy import String, Boolean, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base
import enum

class UserRole(str, enum.Enum):
    Operator = "Operator"
    Supervisor = "Supervisor"
    Management = "Management"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLAlchemyEnum(UserRole), nullable=False, default=UserRole.Operator
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
