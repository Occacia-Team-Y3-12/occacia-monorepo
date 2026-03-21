"""add google calendar oauth tokens

Revision ID: 7f6c1d2e9a4b
Revises: b13e35cade5d
Create Date: 2026-03-15 00:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7f6c1d2e9a4b"
down_revision: str | None = "b13e35cade5d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("calendar_account_email", sa.String(), nullable=True))
    op.add_column(
        "customers", sa.Column("calendar_access_token_encrypted", sa.String(), nullable=True)
    )
    op.add_column(
        "customers", sa.Column("calendar_refresh_token_encrypted", sa.String(), nullable=True)
    )
    op.add_column(
        "customers",
        sa.Column("calendar_token_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("customers", sa.Column("calendar_token_scope", sa.String(), nullable=True))
    op.add_column("customers", sa.Column("calendar_token_type", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("customers", "calendar_token_type")
    op.drop_column("customers", "calendar_token_scope")
    op.drop_column("customers", "calendar_token_expires_at")
    op.drop_column("customers", "calendar_refresh_token_encrypted")
    op.drop_column("customers", "calendar_access_token_encrypted")
    op.drop_column("customers", "calendar_account_email")
