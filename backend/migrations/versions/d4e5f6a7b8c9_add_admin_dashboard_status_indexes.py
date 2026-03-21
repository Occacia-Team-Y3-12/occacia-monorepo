"""Add status indexes for admin dashboard counts

Revision ID: d4e5f6a7b8c9
Revises: f3c1b7a9d2e4
Create Date: 2026-03-21 08:15:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "f3c1b7a9d2e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_users_status", "users", ["status"], unique=False)
    op.create_index("ix_vendors_approval_status", "vendors", ["approval_status"], unique=False)
    op.create_index("ix_events_status", "events", ["status"], unique=False)
    op.create_index(
        "ix_package_execution_requests_status",
        "package_execution_requests",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_package_execution_requests_status", table_name="package_execution_requests")
    op.drop_index("ix_events_status", table_name="events")
    op.drop_index("ix_vendors_approval_status", table_name="vendors")
    op.drop_index("ix_users_status", table_name="users")
