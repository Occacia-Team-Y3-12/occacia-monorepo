"""Add admin email verification fields

Revision ID: f9c2a1b4d7e8
Revises: f3c1b7a9d2e4
Create Date: 2026-03-26 21:05:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f9c2a1b4d7e8"
down_revision: str | Sequence[str] | None = "f3c1b7a9d2e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "admins",
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "admins",
        sa.Column("status", sa.String(), nullable=False, server_default="ACTIVE"),
    )
    op.add_column(
        "admins",
        sa.Column("verification_token", sa.String(), nullable=True),
    )
    op.add_column(
        "admins",
        sa.Column("verification_token_expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.execute("UPDATE admins SET email_verified = TRUE WHERE email_verified IS NULL")
    op.execute("UPDATE admins SET status = 'ACTIVE' WHERE status IS NULL OR status = ''")

    op.alter_column("admins", "email_verified", server_default=sa.false())
    op.alter_column("admins", "status", server_default="PENDING")


def downgrade() -> None:
    op.drop_column("admins", "verification_token_expires_at")
    op.drop_column("admins", "verification_token")
    op.drop_column("admins", "status")
    op.drop_column("admins", "email_verified")
