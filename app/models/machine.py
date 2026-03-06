import uuid
from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from app.db.postgres import Base


class MachineMetadata(Base):
    __tablename__ = "machine_metadata"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False, index=True)
    sensor_type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="active", index=True)
    created_at = Column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )
