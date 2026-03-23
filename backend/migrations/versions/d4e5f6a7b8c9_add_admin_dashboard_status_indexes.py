"""Add status indexes for admin dashboard counts

Revision ID: d4e5f6a7b8c9
Revises: f3c1b7a9d2e4
Create Date: 2026-03-21 08:15:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "d4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "f3c1b7a9d2e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return inspector.has_table(table_name)


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _table_exists(table_name):
        return False
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str]) -> None:
    if not _table_exists(table_name):
        return
    if not _index_exists(table_name, index_name):
        op.create_index(index_name, table_name, columns, unique=False)


def _drop_index_if_exists(index_name: str, table_name: str) -> None:
    if not _table_exists(table_name):
        return
    if _index_exists(table_name, index_name):
        op.drop_index(index_name, table_name=table_name)


def upgrade() -> None:
    _create_index_if_missing("ix_users_status", "users", ["status"])
    _create_index_if_missing("ix_vendors_approval_status", "vendors", ["approval_status"])
    _create_index_if_missing("ix_events_status", "events", ["status"])
    _create_index_if_missing(
        "ix_package_execution_requests_status",
        "package_execution_requests",
        ["status"],
    )


def downgrade() -> None:
    _drop_index_if_exists("ix_package_execution_requests_status", "package_execution_requests")
    _drop_index_if_exists("ix_events_status", "events")
    _drop_index_if_exists("ix_vendors_approval_status", "vendors")
    _drop_index_if_exists("ix_users_status", "users")
