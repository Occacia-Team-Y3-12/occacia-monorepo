"""Expand notifications for queueing and retries

Revision ID: a2c4f6e8b9d1
Revises: 9a6b3d4c5e1f
Create Date: 2026-03-21 13:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a2c4f6e8b9d1"
down_revision: Union[str, Sequence[str], None] = "9a6b3d4c5e1f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("recipient_email", sa.String(), nullable=True))
    op.add_column("notifications", sa.Column("recipient_name", sa.String(), nullable=True))
    op.add_column("notifications", sa.Column("subject", sa.String(), nullable=True))
    op.add_column("notifications", sa.Column("body_text", sa.Text(), nullable=True))
    op.add_column("notifications", sa.Column("body_html", sa.Text(), nullable=True))
    op.add_column("notifications", sa.Column("provider", sa.String(), nullable=True))
    op.add_column("notifications", sa.Column("provider_message_id", sa.String(), nullable=True))
    op.add_column("notifications", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("notifications", sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="4"))
    op.add_column("notifications", sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("notifications", sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True))

    op.execute("UPDATE notifications SET recipient_email = '', subject = type, body_text = ''")

    op.alter_column("notifications", "recipient_email", nullable=False)
    op.alter_column("notifications", "subject", nullable=False)
    op.alter_column("notifications", "body_text", nullable=False)

    op.create_index(op.f("ix_notifications_next_attempt_at"), "notifications", ["next_attempt_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notifications_next_attempt_at"), table_name="notifications")
    op.drop_column("notifications", "next_attempt_at")
    op.drop_column("notifications", "last_attempt_at")
    op.drop_column("notifications", "max_attempts")
    op.drop_column("notifications", "attempt_count")
    op.drop_column("notifications", "provider_message_id")
    op.drop_column("notifications", "provider")
    op.drop_column("notifications", "body_html")
    op.drop_column("notifications", "body_text")
    op.drop_column("notifications", "subject")
    op.drop_column("notifications", "recipient_name")
    op.drop_column("notifications", "recipient_email")
