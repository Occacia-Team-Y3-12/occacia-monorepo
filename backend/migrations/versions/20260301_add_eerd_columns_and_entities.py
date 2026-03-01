"""Add EERD columns and new entity tables.

Revision ID: 20260301_eerd_entities
Revises:
Create Date: 2026-03-01
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260301_eerd_entities"
down_revision = None
branch_labels = None
depends_on = None


def _has_table(inspector: sa.Inspector, name: str) -> bool:
    return name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table: str, column: str) -> bool:
    return any(col["name"] == column for col in inspector.get_columns(table))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "vendors"):
        if not _has_column(inspector, "vendors", "vendor_id"):
            op.add_column("vendors", sa.Column("vendor_id", sa.String(), nullable=True))
            op.create_index("ix_vendors_vendor_id", "vendors", ["vendor_id"], unique=True)
        if not _has_column(inspector, "vendors", "display_name"):
            op.add_column("vendors", sa.Column("display_name", sa.String(), nullable=True))
        if not _has_column(inspector, "vendors", "contact_phone"):
            op.add_column("vendors", sa.Column("contact_phone", sa.String(), nullable=True))
        if not _has_column(inspector, "vendors", "approval_status"):
            op.add_column(
                "vendors",
                sa.Column("approval_status", sa.String(), server_default="PENDING", nullable=True),
            )
        if not _has_column(inspector, "vendors", "approved_at"):
            op.add_column("vendors", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))

    if _has_table(inspector, "customers"):
        if not _has_column(inspector, "customers", "customer_id"):
            op.add_column("customers", sa.Column("customer_id", sa.String(), nullable=True))
            op.create_index("ix_customers_customer_id", "customers", ["customer_id"], unique=True)
        if not _has_column(inspector, "customers", "locale"):
            op.add_column("customers", sa.Column("locale", sa.String(), nullable=True))

    if not _has_table(inspector, "users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.String(), nullable=False, unique=True, index=True),
            sa.Column("email", sa.String(), nullable=False, unique=True, index=True),
            sa.Column("password_hash", sa.String(), nullable=False),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    if not _has_table(inspector, "admins"):
        op.create_table(
            "admins",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("admin_id", sa.String(), nullable=False, unique=True, index=True),
            sa.Column("staff_role", sa.String(), nullable=True),
        )

    if not _has_table(inspector, "personas"):
        op.create_table(
            "personas",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("persona_id", sa.String(), nullable=False, unique=True, index=True),
            sa.Column("customer_id", sa.String(), nullable=False, index=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("preferences_json", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    if not _has_table(inspector, "events"):
        op.create_table(
            "events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("event_id", sa.String(), nullable=False, unique=True, index=True),
            sa.Column("customer_id", sa.String(), nullable=False, index=True),
            sa.Column("event_type", sa.String(), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("location_text", sa.String(), nullable=True),
            sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    if not _has_table(inspector, "event_personas"):
        op.create_table(
            "event_personas",
            sa.Column("event_id", sa.String(), sa.ForeignKey("events.event_id"), primary_key=True),
            sa.Column("persona_id", sa.String(), sa.ForeignKey("personas.persona_id"), primary_key=True),
        )

    if not _has_table(inspector, "chat_messages"):
        op.create_table(
            "chat_messages",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("message_id", sa.String(), nullable=False, unique=True, index=True),
            sa.Column("event_id", sa.String(), nullable=False, index=True),
            sa.Column("sender", sa.String(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        )

    if not _has_table(inspector, "offerings"):
        op.create_table(
            "offerings",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("offering_id", sa.String(), nullable=False, unique=True, index=True),
            sa.Column("vendor_id", sa.String(), nullable=False, index=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("category", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("price", sa.Float(), nullable=False),
            sa.Column("currency", sa.String(), nullable=False),
            sa.Column("unit", sa.String(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("is_available", sa.Boolean(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    if not _has_table(inspector, "tasks"):
        op.create_table(
            "tasks",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("task_id", sa.String(), nullable=False, unique=True, index=True),
            sa.Column("event_id", sa.String(), nullable=False, index=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("budget_min", sa.Float(), nullable=True),
            sa.Column("budget_max", sa.Float(), nullable=True),
            sa.Column("currency", sa.String(), nullable=False),
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
        )

    if not _has_table(inspector, "recommendation_packages"):
        op.create_table(
            "recommendation_packages",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("package_id", sa.String(), nullable=False, unique=True, index=True),
            sa.Column("event_id", sa.String(), nullable=False, index=True),
            sa.Column("package_type", sa.String(), nullable=False),
            sa.Column("package_total_price", sa.Float(), nullable=False),
            sa.Column("currency", sa.String(), nullable=False),
            sa.Column("is_customized", sa.Boolean(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    if not _has_table(inspector, "task_recommendations"):
        op.create_table(
            "task_recommendations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("recommendation_id", sa.String(), nullable=False, unique=True, index=True),
            sa.Column("event_id", sa.String(), nullable=False, index=True),
            sa.Column("task_id", sa.String(), nullable=False, index=True),
            sa.Column("offering_id", sa.String(), nullable=False, index=True),
            sa.Column("score", sa.Float(), nullable=False),
            sa.Column("rank", sa.Integer(), nullable=False),
            sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        )

    if not _has_table(inspector, "package_items"):
        op.create_table(
            "package_items",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("package_item_id", sa.String(), nullable=False, unique=True, index=True),
            sa.Column("package_id", sa.String(), nullable=False, index=True),
            sa.Column("task_id", sa.String(), nullable=False, index=True),
            sa.Column("offering_id", sa.String(), nullable=False, index=True),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("unit_price", sa.Float(), nullable=False),
            sa.Column("line_total", sa.Float(), nullable=False),
        )

    if not _has_table(inspector, "package_execution_requests"):
        op.create_table(
            "package_execution_requests",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("execution_request_id", sa.String(), nullable=False, unique=True, index=True),
            sa.Column("event_id", sa.String(), nullable=False, index=True),
            sa.Column("package_id", sa.String(), nullable=False, index=True),
            sa.Column("idempotency_key", sa.String(), nullable=False, unique=True, index=True),
            sa.Column("currency", sa.String(), nullable=False),
            sa.Column("package_total_price", sa.Float(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status_updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    if not _has_table(inspector, "task_requests"):
        op.create_table(
            "task_requests",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("request_id", sa.String(), nullable=False, unique=True, index=True),
            sa.Column("task_id", sa.String(), nullable=False, index=True),
            sa.Column("vendor_id", sa.String(), nullable=False, index=True),
            sa.Column("offering_id", sa.String(), nullable=False, index=True),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("respond_by", sa.DateTime(timezone=True), nullable=True),
            sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("response_note", sa.Text(), nullable=True),
            sa.Column("attempt_no", sa.Integer(), nullable=False),
        )

    if not _has_table(inspector, "support_notes"):
        op.create_table(
            "support_notes",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("note_id", sa.String(), nullable=False, unique=True, index=True),
            sa.Column("admin_id", sa.String(), nullable=False, index=True),
            sa.Column("event_id", sa.String(), nullable=True, index=True),
            sa.Column("task_id", sa.String(), nullable=True, index=True),
            sa.Column("vendor_id", sa.String(), nullable=True, index=True),
            sa.Column("action_type", sa.String(), nullable=False),
            sa.Column("note", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for table in [
        "support_notes",
        "task_requests",
        "package_execution_requests",
        "package_items",
        "task_recommendations",
        "recommendation_packages",
        "tasks",
        "offerings",
        "chat_messages",
        "event_personas",
        "events",
        "personas",
        "admins",
        "users",
    ]:
        if _has_table(inspector, table):
            op.drop_table(table)

    if _has_table(inspector, "customers"):
        if _has_column(inspector, "customers", "locale"):
            op.drop_column("customers", "locale")
        if _has_column(inspector, "customers", "customer_id"):
            op.drop_index("ix_customers_customer_id", table_name="customers")
            op.drop_column("customers", "customer_id")

    if _has_table(inspector, "vendors"):
        if _has_column(inspector, "vendors", "approved_at"):
            op.drop_column("vendors", "approved_at")
        if _has_column(inspector, "vendors", "approval_status"):
            op.drop_column("vendors", "approval_status")
        if _has_column(inspector, "vendors", "contact_phone"):
            op.drop_column("vendors", "contact_phone")
        if _has_column(inspector, "vendors", "display_name"):
            op.drop_column("vendors", "display_name")
        if _has_column(inspector, "vendors", "vendor_id"):
            op.drop_index("ix_vendors_vendor_id", table_name="vendors")
            op.drop_column("vendors", "vendor_id")