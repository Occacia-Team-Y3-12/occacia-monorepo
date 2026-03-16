"""Add customer event and recommendation tables

Revision ID: 6d7a1c9f3b42
Revises: b13e35cade5d
Create Date: 2026-03-15 16:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6d7a1c9f3b42"
down_revision: Union[str, None] = "b13e35cade5d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(), nullable=True),
        sa.Column("customer_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location_text", sa.String(), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timezone", sa.String(), nullable=True),
        sa.Column("is_all_day", sa.Boolean(), nullable=False),
        sa.Column("recurrence_rule", sa.String(), nullable=True),
        sa.Column("recurrence_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recurrence_count", sa.Integer(), nullable=True),
        sa.Column("reminders_enabled", sa.Boolean(), nullable=False),
        sa.Column("reminder_channels", sa.JSON(), nullable=False),
        sa.Column("reminder_offsets", sa.JSON(), nullable=False),
        sa.Column("reminder_schedule_status", sa.String(), nullable=True),
        sa.Column("calendar_sync_state", sa.String(), nullable=False),
        sa.Column("calendar_sync_provider", sa.String(), nullable=True),
        sa.Column("calendar_sync_calendar_id", sa.String(), nullable=True),
        sa.Column("external_calendar_event_id", sa.String(), nullable=True),
        sa.Column("calendar_last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("calendar_last_sync_status", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_events_event_id"), "events", ["event_id"], unique=True)
    op.create_index(op.f("ix_events_customer_id"), "events", ["customer_id"], unique=False)
    op.create_index(op.f("ix_events_id"), "events", ["id"], unique=False)

    op.create_table(
        "event_personas",
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("persona_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.event_id"]),
        sa.ForeignKeyConstraint(["persona_id"], ["personas.persona_id"]),
        sa.PrimaryKeyConstraint("event_id", "persona_id"),
    )

    op.create_table(
        "event_chat_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.String(), nullable=True),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("sender", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_event_chat_messages_id"), "event_chat_messages", ["id"], unique=False)
    op.create_index(op.f("ix_event_chat_messages_message_id"), "event_chat_messages", ["message_id"], unique=True)
    op.create_index(op.f("ix_event_chat_messages_event_id"), "event_chat_messages", ["event_id"], unique=False)

    op.create_table(
        "offerings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("offering_id", sa.String(), nullable=True),
        sa.Column("vendor_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_offerings_id"), "offerings", ["id"], unique=False)
    op.create_index(op.f("ix_offerings_offering_id"), "offerings", ["offering_id"], unique=True)
    op.create_index(op.f("ix_offerings_vendor_id"), "offerings", ["vendor_id"], unique=False)

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.String(), nullable=True),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("budget_min", sa.Float(), nullable=True),
        sa.Column("budget_max", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("needs_vendor", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("selected_offering_id", sa.String(), nullable=True),
        sa.Column("assigned_vendor_id", sa.String(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("status_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tasks_id"), "tasks", ["id"], unique=False)
    op.create_index(op.f("ix_tasks_task_id"), "tasks", ["task_id"], unique=True)
    op.create_index(op.f("ix_tasks_event_id"), "tasks", ["event_id"], unique=False)

    op.create_table(
        "recommendation_packages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("package_id", sa.String(), nullable=True),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("package_type", sa.String(), nullable=False),
        sa.Column("package_total_price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("is_customized", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recommendation_packages_id"), "recommendation_packages", ["id"], unique=False)
    op.create_index(op.f("ix_recommendation_packages_package_id"), "recommendation_packages", ["package_id"], unique=True)
    op.create_index(op.f("ix_recommendation_packages_event_id"), "recommendation_packages", ["event_id"], unique=False)

    op.create_table(
        "task_recommendations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recommendation_id", sa.String(), nullable=True),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("offering_id", sa.String(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_recommendations_id"), "task_recommendations", ["id"], unique=False)
    op.create_index(op.f("ix_task_recommendations_recommendation_id"), "task_recommendations", ["recommendation_id"], unique=True)
    op.create_index(op.f("ix_task_recommendations_event_id"), "task_recommendations", ["event_id"], unique=False)
    op.create_index(op.f("ix_task_recommendations_task_id"), "task_recommendations", ["task_id"], unique=False)
    op.create_index(op.f("ix_task_recommendations_offering_id"), "task_recommendations", ["offering_id"], unique=False)

    op.create_table(
        "package_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("package_item_id", sa.String(), nullable=True),
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("offering_id", sa.String(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("line_total", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["offering_id"], ["offerings.offering_id"]),
        sa.ForeignKeyConstraint(["package_id"], ["recommendation_packages.package_id"]),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.task_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_package_items_id"), "package_items", ["id"], unique=False)
    op.create_index(op.f("ix_package_items_package_item_id"), "package_items", ["package_item_id"], unique=True)
    op.create_index(op.f("ix_package_items_package_id"), "package_items", ["package_id"], unique=False)

    op.create_table(
        "package_execution_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("execution_request_id", sa.String(), nullable=True),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("package_total_price", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_package_execution_requests_id"), "package_execution_requests", ["id"], unique=False)
    op.create_index(op.f("ix_package_execution_requests_execution_request_id"), "package_execution_requests", ["execution_request_id"], unique=True)
    op.create_index(op.f("ix_package_execution_requests_event_id"), "package_execution_requests", ["event_id"], unique=False)
    op.create_index(op.f("ix_package_execution_requests_package_id"), "package_execution_requests", ["package_id"], unique=False)
    op.create_index(op.f("ix_package_execution_requests_idempotency_key"), "package_execution_requests", ["idempotency_key"], unique=True)

    op.create_table(
        "task_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.String(), nullable=True),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("vendor_id", sa.String(), nullable=False),
        sa.Column("offering_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("respond_by", sa.DateTime(timezone=True), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_note", sa.Text(), nullable=True),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["offering_id"], ["offerings.offering_id"]),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.task_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_requests_id"), "task_requests", ["id"], unique=False)
    op.create_index(op.f("ix_task_requests_request_id"), "task_requests", ["request_id"], unique=True)
    op.create_index(op.f("ix_task_requests_task_id"), "task_requests", ["task_id"], unique=False)
    op.create_index(op.f("ix_task_requests_vendor_id"), "task_requests", ["vendor_id"], unique=False)
    op.create_index(op.f("ix_task_requests_offering_id"), "task_requests", ["offering_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_task_requests_offering_id"), table_name="task_requests")
    op.drop_index(op.f("ix_task_requests_vendor_id"), table_name="task_requests")
    op.drop_index(op.f("ix_task_requests_task_id"), table_name="task_requests")
    op.drop_index(op.f("ix_task_requests_request_id"), table_name="task_requests")
    op.drop_index(op.f("ix_task_requests_id"), table_name="task_requests")
    op.drop_table("task_requests")

    op.drop_index(op.f("ix_package_execution_requests_idempotency_key"), table_name="package_execution_requests")
    op.drop_index(op.f("ix_package_execution_requests_package_id"), table_name="package_execution_requests")
    op.drop_index(op.f("ix_package_execution_requests_event_id"), table_name="package_execution_requests")
    op.drop_index(op.f("ix_package_execution_requests_execution_request_id"), table_name="package_execution_requests")
    op.drop_index(op.f("ix_package_execution_requests_id"), table_name="package_execution_requests")
    op.drop_table("package_execution_requests")

    op.drop_index(op.f("ix_package_items_package_id"), table_name="package_items")
    op.drop_index(op.f("ix_package_items_package_item_id"), table_name="package_items")
    op.drop_index(op.f("ix_package_items_id"), table_name="package_items")
    op.drop_table("package_items")

    op.drop_index(op.f("ix_task_recommendations_offering_id"), table_name="task_recommendations")
    op.drop_index(op.f("ix_task_recommendations_task_id"), table_name="task_recommendations")
    op.drop_index(op.f("ix_task_recommendations_event_id"), table_name="task_recommendations")
    op.drop_index(op.f("ix_task_recommendations_recommendation_id"), table_name="task_recommendations")
    op.drop_index(op.f("ix_task_recommendations_id"), table_name="task_recommendations")
    op.drop_table("task_recommendations")

    op.drop_index(op.f("ix_recommendation_packages_event_id"), table_name="recommendation_packages")
    op.drop_index(op.f("ix_recommendation_packages_package_id"), table_name="recommendation_packages")
    op.drop_index(op.f("ix_recommendation_packages_id"), table_name="recommendation_packages")
    op.drop_table("recommendation_packages")

    op.drop_index(op.f("ix_tasks_event_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_task_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_id"), table_name="tasks")
    op.drop_table("tasks")

    op.drop_index(op.f("ix_offerings_vendor_id"), table_name="offerings")
    op.drop_index(op.f("ix_offerings_offering_id"), table_name="offerings")
    op.drop_index(op.f("ix_offerings_id"), table_name="offerings")
    op.drop_table("offerings")

    op.drop_index(op.f("ix_event_chat_messages_event_id"), table_name="event_chat_messages")
    op.drop_index(op.f("ix_event_chat_messages_message_id"), table_name="event_chat_messages")
    op.drop_index(op.f("ix_event_chat_messages_id"), table_name="event_chat_messages")
    op.drop_table("event_chat_messages")

    op.drop_table("event_personas")

    op.drop_index(op.f("ix_events_id"), table_name="events")
    op.drop_index(op.f("ix_events_customer_id"), table_name="events")
    op.drop_index(op.f("ix_events_event_id"), table_name="events")
    op.drop_table("events")
