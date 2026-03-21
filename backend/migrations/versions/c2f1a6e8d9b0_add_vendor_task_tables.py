"""add vendor task tables

Revision ID: c2f1a6e8d9b0
Revises: 4de2b30ff548
Create Date: 2026-03-21 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2f1a6e8d9b0"
down_revision: Union[str, None] = "4de2b30ff548"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vendor_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column("offering_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending_response",
                "assigned",
                "completed",
                "rejected",
                "expired",
                name="taskstatus",
            ),
            nullable=True,
        ),
        sa.Column(
            "priority",
            sa.Enum("high", "medium", "low", name="taskpriority"),
            nullable=True,
        ),
        sa.Column("budget_min", sa.Numeric(10, 2), nullable=True),
        sa.Column("budget_max", sa.Numeric(10, 2), nullable=True),
        sa.Column("agreed_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("expiry_date", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("responded_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["offering_id"], ["offerings.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vendor_tasks_id"), "vendor_tasks", ["id"], unique=False)
    op.create_index(op.f("ix_vendor_tasks_vendor_id"), "vendor_tasks", ["vendor_id"], unique=False)
    op.create_index(op.f("ix_vendor_tasks_status"), "vendor_tasks", ["status"], unique=False)

    op.create_table(
        "vendor_task_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("sender_type", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["vendor_tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vendor_task_messages_id"), "vendor_task_messages", ["id"], unique=False)
    op.create_index(op.f("ix_vendor_task_messages_task_id"), "vendor_task_messages", ["task_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_vendor_task_messages_task_id"), table_name="vendor_task_messages")
    op.drop_index(op.f("ix_vendor_task_messages_id"), table_name="vendor_task_messages")
    op.drop_table("vendor_task_messages")

    op.drop_index(op.f("ix_vendor_tasks_status"), table_name="vendor_tasks")
    op.drop_index(op.f("ix_vendor_tasks_vendor_id"), table_name="vendor_tasks")
    op.drop_index(op.f("ix_vendor_tasks_id"), table_name="vendor_tasks")
    op.drop_table("vendor_tasks")
