"""add wipe execution job table

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-27
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "wipeexecutionjob",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("target_serial", sa.String(), nullable=False),
        sa.Column("storage_type", sa.String(), nullable=False),
        sa.Column("execution_mode", sa.String(), nullable=False),
        sa.Column("standard_profile", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("approved_by", sa.String(), nullable=True),
        sa.Column("approval_note", sa.String(), nullable=False),
        sa.Column("rejected_by", sa.String(), nullable=True),
        sa.Column("rejection_note", sa.String(), nullable=False),
        sa.Column("canceled_by", sa.String(), nullable=True),
        sa.Column("cancel_note", sa.String(), nullable=False),
        sa.Column("device_fingerprint", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_wipeexecutionjob_asset_id", "wipeexecutionjob", ["asset_id"])


def downgrade() -> None:
    op.drop_index("ix_wipeexecutionjob_asset_id", table_name="wipeexecutionjob")
    op.drop_table("wipeexecutionjob")
