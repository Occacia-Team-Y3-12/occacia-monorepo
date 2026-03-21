"""Merge notifications and task request heads

Revision ID: f3c1b7a9d2e4
Revises: e1a4c7d9f2b1, a2c4f6e8b9d1
Create Date: 2026-03-21 06:20:00.000000
"""

from collections.abc import Sequence

revision: str = "f3c1b7a9d2e4"
down_revision: str | Sequence[str] | None = ("e1a4c7d9f2b1", "a2c4f6e8b9d1")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
