"""add module orchestration and agent session tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-27
"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agentsession",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("agent_id", sa.String(), nullable=False, unique=True),
        sa.Column("asset_id", sa.String(), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("mode", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_agentsession_agent_id", "agentsession", ["agent_id"])
    op.create_index("ix_agentsession_asset_id", "agentsession", ["asset_id"])

    op.create_table(
        "operationrun",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("module", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("asset_id", sa.String(), nullable=False),
        sa.Column("operator", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False),
        sa.Column("parameters_json", sa.String(), nullable=False),
        sa.Column("result_json", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_operationrun_module", "operationrun", ["module"])
    op.create_index("ix_operationrun_tenant_id", "operationrun", ["tenant_id"])
    op.create_index("ix_operationrun_asset_id", "operationrun", ["asset_id"])

    op.create_table(
        "operationticketlink",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("operation_run_id", sa.Integer(), nullable=False),
        sa.Column("ndesk_ticket_id", sa.String(), nullable=False),
        sa.Column("relation", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_operationticketlink_operation_run_id", "operationticketlink", ["operation_run_id"])
    op.create_index("ix_operationticketlink_ndesk_ticket_id", "operationticketlink", ["ndesk_ticket_id"])


def downgrade() -> None:
    op.drop_index("ix_operationticketlink_ndesk_ticket_id", table_name="operationticketlink")
    op.drop_index("ix_operationticketlink_operation_run_id", table_name="operationticketlink")
    op.drop_table("operationticketlink")

    op.drop_index("ix_operationrun_asset_id", table_name="operationrun")
    op.drop_index("ix_operationrun_tenant_id", table_name="operationrun")
    op.drop_index("ix_operationrun_module", table_name="operationrun")
    op.drop_table("operationrun")

    op.drop_index("ix_agentsession_asset_id", table_name="agentsession")
    op.drop_index("ix_agentsession_agent_id", table_name="agentsession")
    op.drop_table("agentsession")
