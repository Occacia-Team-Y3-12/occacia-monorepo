"""merge divergent database heads

Revision ID: 4de2b30ff548
Revises: 20260311_uc13_columns
Create Date: 2026-03-12 09:53:56.001212

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4de2b30ff548'
down_revision: Union[str, None] = '20260311_uc13_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass