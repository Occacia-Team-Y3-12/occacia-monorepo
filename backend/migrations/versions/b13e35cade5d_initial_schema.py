"""Initial schema

Revision ID: b13e35cade5d
Revises:
Create Date: 2026-03-14 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b13e35cade5d"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_user_id"), "users", ["user_id"], unique=True)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.String(), nullable=True),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("locale", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("email_verified", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("verification_token", sa.String(), nullable=True),
        sa.Column("verification_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("calendar_provider", sa.String(), nullable=True),
        sa.Column("calendar_default_id", sa.String(), nullable=True),
        sa.Column("calendar_connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("calendar_last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("calendar_oauth_state", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_customers_id"), "customers", ["id"], unique=False)
    op.create_index(op.f("ix_customers_customer_id"), "customers", ["customer_id"], unique=True)
    op.create_index(op.f("ix_customers_email"), "customers", ["email"], unique=True)

    op.create_table(
        "vendors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vendor_id", sa.String(), nullable=True),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("contact_phone", sa.String(), nullable=True),
        sa.Column("approval_status", sa.String(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("business_name", sa.String(), nullable=True),
        sa.Column("location_base", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=True),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vendors_id"), "vendors", ["id"], unique=False)
    op.create_index(op.f("ix_vendors_vendor_id"), "vendors", ["vendor_id"], unique=True)
    op.create_index(op.f("ix_vendors_business_name"), "vendors", ["business_name"], unique=False)
    op.create_index(op.f("ix_vendors_email"), "vendors", ["email"], unique=True)

    op.create_table(
        "personas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("persona_id", sa.String(), nullable=True),
        sa.Column("customer_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("relationship", sa.String(), nullable=True),
        sa.Column("birthday", sa.DateTime(timezone=True), nullable=True),
        sa.Column("personality", sa.Text(), nullable=True),
        sa.Column("preferences_json", sa.JSON(), nullable=True),
        sa.Column("food_preferences", sa.JSON(), nullable=True),
        sa.Column("color_preferences", sa.JSON(), nullable=True),
        sa.Column("music_preferences", sa.JSON(), nullable=True),
        sa.Column("personality_tags", sa.JSON(), nullable=True),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_personas_id"), "personas", ["id"], unique=False)
    op.create_index(op.f("ix_personas_persona_id"), "personas", ["persona_id"], unique=True)
    op.create_index(op.f("ix_personas_customer_id"), "personas", ["customer_id"], unique=False)

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("customer_id", sa.String(), nullable=True),
        sa.Column("user_message", sa.Text(), nullable=True),
        sa.Column("ai_message", sa.Text(), nullable=True),
        sa.Column("missing_info", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_messages_id"), "chat_messages", ["id"], unique=False)
    op.create_index(
        op.f("ix_chat_messages_session_id"), "chat_messages", ["session_id"], unique=False
    )
    op.create_index(
        op.f("ix_chat_messages_customer_id"), "chat_messages", ["customer_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_chat_messages_customer_id"), table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_session_id"), table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_id"), table_name="chat_messages")
    op.drop_table("chat_messages")

    op.drop_index(op.f("ix_personas_customer_id"), table_name="personas")
    op.drop_index(op.f("ix_personas_persona_id"), table_name="personas")
    op.drop_index(op.f("ix_personas_id"), table_name="personas")
    op.drop_table("personas")

    op.drop_index(op.f("ix_vendors_email"), table_name="vendors")
    op.drop_index(op.f("ix_vendors_business_name"), table_name="vendors")
    op.drop_index(op.f("ix_vendors_vendor_id"), table_name="vendors")
    op.drop_index(op.f("ix_vendors_id"), table_name="vendors")
    op.drop_table("vendors")

    op.drop_index(op.f("ix_customers_email"), table_name="customers")
    op.drop_index(op.f("ix_customers_customer_id"), table_name="customers")
    op.drop_index(op.f("ix_customers_id"), table_name="customers")
    op.drop_table("customers")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_user_id"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
