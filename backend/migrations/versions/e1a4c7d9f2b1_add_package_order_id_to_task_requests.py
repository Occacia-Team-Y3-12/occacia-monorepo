"""Add package order id to task requests

Revision ID: e1a4c7d9f2b1
Revises: c8f4d9b2a1e7
Create Date: 2026-03-20 21:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e1a4c7d9f2b1"
down_revision: str | Sequence[str] | None = "c8f4d9b2a1e7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("task_requests", sa.Column("package_order_id", sa.String(), nullable=True))
    op.create_index(
        op.f("ix_task_requests_package_order_id"),
        "task_requests",
        ["package_order_id"],
        unique=False,
    )
    op.execute("UPDATE task_requests SET package_order_id = '' WHERE package_order_id IS NULL")
    op.alter_column("task_requests", "package_order_id", nullable=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_task_requests_package_order_id"), table_name="task_requests")
    op.drop_column("task_requests", "package_order_id")
