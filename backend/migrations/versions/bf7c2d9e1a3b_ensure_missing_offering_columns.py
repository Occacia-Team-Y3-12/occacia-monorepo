"""ensure missing offering columns

Revision ID: bf7c2d9e1a3b
Revises: 60f925bbc071
Create Date: 2026-03-23 00:30:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bf7c2d9e1a3b'
down_revision = '60f925bbc071'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Safely add missing columns to 'offerings' table
    op.execute("ALTER TABLE offerings ADD COLUMN IF NOT EXISTS quality_tier VARCHAR NOT NULL DEFAULT 'MEDIUM'")
    op.execute("ALTER TABLE offerings ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now()")


def downgrade() -> None:
    op.drop_column('offerings', 'created_at')
    op.drop_column('offerings', 'quality_tier')
