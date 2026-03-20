"""Add custom package metadata

Revision ID: c8f4d9b2a1e7
Revises: 4de2b30ff548
Create Date: 2026-03-20 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8f4d9b2a1e7"
down_revision: Union[str, Sequence[str], None] = "4de2b30ff548"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("recommendation_packages", sa.Column("base_package_id", sa.String(), nullable=True))
    op.add_column("recommendation_packages", sa.Column("created_by_customer_id", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("recommendation_packages", "created_by_customer_id")
    op.drop_column("recommendation_packages", "base_package_id")
