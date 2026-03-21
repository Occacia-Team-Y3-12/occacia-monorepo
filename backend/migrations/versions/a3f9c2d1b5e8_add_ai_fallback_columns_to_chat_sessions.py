"""Add AI fallback columns to chat sessions

Revision ID: a3f9c2d1b5e8
Revises: f3c1b7a9d2e4
Create Date: 2026-03-21 20:49:06.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a3f9c2d1b5e8"
down_revision: str | Sequence[str] | None = "f3c1b7a9d2e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    table_name = "chat_sessions"
    table_ref = bind.execute(sa.text("SELECT to_regclass('public.chat_sessions')")).scalar()
    table_exists = table_ref is not None

    if not table_exists:
        op.create_table(
            table_name,
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("event_id", sa.String(), nullable=False),
            sa.Column("step", sa.String(), nullable=False, server_default="0"),
            sa.Column("persona_draft", sa.Text(), nullable=True),
            sa.Column("chosen_persona_id", sa.String(), nullable=True),
            sa.Column("venue_data", sa.Text(), nullable=True),
            sa.Column("rec_ids", sa.Text(), nullable=True),
            sa.Column("gift_rec_ids", sa.Text(), nullable=True),
            sa.Column("pending_save", sa.Text(), nullable=True),
            sa.Column("booking_id", sa.String(), nullable=True),
            sa.Column("ai_fallback_venues", sa.Text(), nullable=True),
            sa.Column("ai_fallback_gifts", sa.Text(), nullable=True),
            sa.Column("is_ai_fallback", sa.String(), nullable=True, server_default="false"),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_chat_sessions_id"), table_name, ["id"], unique=False)
        op.create_index(op.f("ix_chat_sessions_event_id"), table_name, ["event_id"], unique=True)
        return

    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    if "ai_fallback_venues" not in existing_columns:
        op.add_column(
            table_name,
            sa.Column("ai_fallback_venues", sa.Text(), nullable=True),
        )
    if "ai_fallback_gifts" not in existing_columns:
        op.add_column(
            table_name,
            sa.Column("ai_fallback_gifts", sa.Text(), nullable=True),
        )
    if "is_ai_fallback" not in existing_columns:
        op.add_column(
            table_name,
            sa.Column("is_ai_fallback", sa.String(), nullable=True, server_default="false"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    table_name = "chat_sessions"
    table_ref = bind.execute(sa.text("SELECT to_regclass('public.chat_sessions')")).scalar()
    if table_ref is None:
        return

    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    if "is_ai_fallback" in existing_columns:
        op.drop_column(table_name, "is_ai_fallback")
    if "ai_fallback_gifts" in existing_columns:
        op.drop_column(table_name, "ai_fallback_gifts")
    if "ai_fallback_venues" in existing_columns:
        op.drop_column(table_name, "ai_fallback_venues")
