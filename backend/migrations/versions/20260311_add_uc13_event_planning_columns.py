"""Add UC-13 schedule, reminders, and calendar sync columns.

Revision ID: 20260311_uc13_columns
Revises: 20260301_eerd_entities
Create Date: 2026-03-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260311_uc13_columns"
down_revision = "20260301_eerd_entities"
branch_labels = None
depends_on = None


def _has_column(inspector: sa.Inspector, table: str, column: str) -> bool:
    return any(col["name"] == column for col in inspector.get_columns(table))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    event_columns = {
        "timezone": sa.Column("timezone", sa.String(), nullable=True),
        "is_all_day": sa.Column("is_all_day", sa.Boolean(), nullable=False, server_default=sa.false()),
        "recurrence_rule": sa.Column("recurrence_rule", sa.String(), nullable=True),
        "recurrence_until": sa.Column("recurrence_until", sa.DateTime(timezone=True), nullable=True),
        "recurrence_count": sa.Column("recurrence_count", sa.Integer(), nullable=True),
        "reminders_enabled": sa.Column("reminders_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        "reminder_channels": sa.Column("reminder_channels", sa.JSON(), nullable=True),
        "reminder_offsets": sa.Column("reminder_offsets", sa.JSON(), nullable=True),
        "reminder_schedule_status": sa.Column("reminder_schedule_status", sa.String(), nullable=True),
        "calendar_sync_state": sa.Column("calendar_sync_state", sa.String(), nullable=False, server_default="DISABLED"),
        "calendar_sync_provider": sa.Column("calendar_sync_provider", sa.String(), nullable=True),
        "calendar_sync_calendar_id": sa.Column("calendar_sync_calendar_id", sa.String(), nullable=True),
        "external_calendar_event_id": sa.Column("external_calendar_event_id", sa.String(), nullable=True),
        "calendar_last_sync_at": sa.Column("calendar_last_sync_at", sa.DateTime(timezone=True), nullable=True),
        "calendar_last_sync_status": sa.Column("calendar_last_sync_status", sa.String(), nullable=True),
    }
    for name, column in event_columns.items():
        if not _has_column(inspector, "events", name):
            op.add_column("events", column)

    customer_columns = {
        "calendar_provider": sa.Column("calendar_provider", sa.String(), nullable=True),
        "calendar_default_id": sa.Column("calendar_default_id", sa.String(), nullable=True),
        "calendar_connected_at": sa.Column("calendar_connected_at", sa.DateTime(timezone=True), nullable=True),
        "calendar_last_sync_at": sa.Column("calendar_last_sync_at", sa.DateTime(timezone=True), nullable=True),
        "calendar_oauth_state": sa.Column("calendar_oauth_state", sa.String(), nullable=True),
    }
    for name, column in customer_columns.items():
        if not _has_column(inspector, "customers", name):
            op.add_column("customers", column)

    if not _has_column(inspector, "tasks", "needs_vendor"):
        op.add_column("tasks", sa.Column("needs_vendor", sa.String(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for column in [
        "needs_vendor",
    ]:
        if _has_column(inspector, "tasks", column):
            op.drop_column("tasks", column)

    for column in [
        "calendar_oauth_state",
        "calendar_last_sync_at",
        "calendar_connected_at",
        "calendar_default_id",
        "calendar_provider",
    ]:
        if _has_column(inspector, "customers", column):
            op.drop_column("customers", column)

    for column in [
        "calendar_last_sync_status",
        "calendar_last_sync_at",
        "external_calendar_event_id",
        "calendar_sync_calendar_id",
        "calendar_sync_provider",
        "calendar_sync_state",
        "reminder_schedule_status",
        "reminder_offsets",
        "reminder_channels",
        "reminders_enabled",
        "recurrence_count",
        "recurrence_until",
        "recurrence_rule",
        "is_all_day",
        "timezone",
    ]:
        if _has_column(inspector, "events", column):
            op.drop_column("events", column)
