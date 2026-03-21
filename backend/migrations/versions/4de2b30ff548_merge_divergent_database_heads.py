"""Merge divergent database heads

Revision ID: 4de2b30ff548
Revises: 6d7a1c9f3b42, 7f6c1d2e9a4b
Create Date: 2026-03-16 02:00:00.000000
"""

from collections.abc import Sequence

revision: str = "4de2b30ff548"
down_revision: str | Sequence[str] | None = ("6d7a1c9f3b42", "7f6c1d2e9a4b")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
