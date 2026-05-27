"""add module evidence table

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-27
"""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "moduleevidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("operation_run_id", sa.Integer(), nullable=False),
        sa.Column("module", sa.String(), nullable=False),
        sa.Column("evidence_type", sa.String(), nullable=False),
        sa.Column("payload_json", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_moduleevidence_operation_run_id", "moduleevidence", ["operation_run_id"])
    op.create_index("ix_moduleevidence_module", "moduleevidence", ["module"])
    op.create_index("ix_moduleevidence_evidence_type", "moduleevidence", ["evidence_type"])


def downgrade() -> None:
    op.drop_index("ix_moduleevidence_evidence_type", table_name="moduleevidence")
    op.drop_index("ix_moduleevidence_module", table_name="moduleevidence")
    op.drop_index("ix_moduleevidence_operation_run_id", table_name="moduleevidence")
    op.drop_table("moduleevidence")
