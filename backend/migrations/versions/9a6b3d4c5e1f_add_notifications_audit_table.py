"""Add notifications audit table

Revision ID: 9a6b3d4c5e1f
Revises: c8f4d9b2a1e7
Create Date: 2026-03-21 10:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9a6b3d4c5e1f"
down_revision: Union[str, Sequence[str], None] = "c8f4d9b2a1e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("notification_id", sa.String(), nullable=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("event_id", sa.String(), nullable=True),
        sa.Column("task_id", sa.String(), nullable=True),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("dedupe_key", sa.String(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notifications_notification_id"), "notifications", ["notification_id"], unique=True)
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)
    op.create_index(op.f("ix_notifications_event_id"), "notifications", ["event_id"], unique=False)
    op.create_index(op.f("ix_notifications_task_id"), "notifications", ["task_id"], unique=False)
    op.create_index(op.f("ix_notifications_type"), "notifications", ["type"], unique=False)
    op.create_index(op.f("ix_notifications_status"), "notifications", ["status"], unique=False)
    op.create_index(op.f("ix_notifications_dedupe_key"), "notifications", ["dedupe_key"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notifications_dedupe_key"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_status"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_type"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_task_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_event_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_notification_id"), table_name="notifications")
    op.drop_table("notifications")
