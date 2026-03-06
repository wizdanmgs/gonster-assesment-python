"""Initial migration

Revision ID: 1e0a9b8c7d6e
Revises: 
Create Date: 2026-03-05 17:18:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1e0a9b8c7d6e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable uuid-ossp extension if not exists
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    op.create_table('machine_metadata',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('sensor_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='active', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_machine_metadata_location'), 'machine_metadata', ['location'], unique=False)
    op.create_index(op.f('ix_machine_metadata_status'), 'machine_metadata', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_machine_metadata_status'), table_name='machine_metadata')
    op.drop_index(op.f('ix_machine_metadata_location'), table_name='machine_metadata')
    op.drop_table('machine_metadata')
