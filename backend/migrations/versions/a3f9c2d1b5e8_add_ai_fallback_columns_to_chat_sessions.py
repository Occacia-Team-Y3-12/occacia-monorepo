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
    op.add_column(
        "chat_sessions",
        sa.Column("ai_fallback_venues", sa.Text(), nullable=True),
    )
    op.add_column(
        "chat_sessions",
        sa.Column("ai_fallback_gifts", sa.Text(), nullable=True),
    )
    op.add_column(
        "chat_sessions",
        sa.Column("is_ai_fallback", sa.String(), nullable=True, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("chat_sessions", "is_ai_fallback")
    op.drop_column("chat_sessions", "ai_fallback_gifts")
    op.drop_column("chat_sessions", "ai_fallback_venues")
