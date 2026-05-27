"""init

Revision ID: 0001
Revises: 
Create Date: 2026-05-27
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("asset",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("asset_id", sa.String(), nullable=False, unique=True),
        sa.Column("serial_number", sa.String(), nullable=False),
        sa.Column("device_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_asset_tenant_id", "asset", ["tenant_id"])
    op.create_index("ix_asset_asset_id", "asset", ["asset_id"])


def downgrade() -> None:
    op.drop_index("ix_asset_asset_id", table_name="asset")
    op.drop_index("ix_asset_tenant_id", table_name="asset")
    op.drop_table("asset")
