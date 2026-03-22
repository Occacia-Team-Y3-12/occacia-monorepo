"""add ai fallback columns to chat sessions

Revision ID: a3f9c2d1b5e8
Revises: 4de2b30ff548
Create Date: 2025-12-16 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a3f9c2d1b5e8'
down_revision = '4de2b30ff548'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'chat_sessions',
        sa.Column('ai_fallback_venues', sa.Text(), nullable=True),
    )
    op.add_column(
        'chat_sessions',
        sa.Column('ai_fallback_gifts', sa.Text(), nullable=True),
    )
    op.add_column(
        'chat_sessions',
        sa.Column('is_ai_fallback', sa.String(), nullable=True, server_default='false'),
    )


def downgrade() -> None:
    op.drop_column('chat_sessions', 'is_ai_fallback')
    op.drop_column('chat_sessions', 'ai_fallback_gifts')
    op.drop_column('chat_sessions', 'ai_fallback_venues')