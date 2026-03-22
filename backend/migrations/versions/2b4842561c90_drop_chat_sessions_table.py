"""drop_chat_sessions_table

Revision ID: 2b4842561c90
Revises: a3f9c2d1b5e8
Create Date: 2026-03-22 23:02:56.687002

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b4842561c90'
down_revision: Union[str, None] = 'a3f9c2d1b5e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('chat_sessions')


def downgrade() -> None:
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(), nullable=False),
        sa.Column('step', sa.String(), nullable=False, server_default='0'),
        sa.Column('persona_draft', sa.Text(), nullable=True),
        sa.Column('chosen_persona_id', sa.String(), nullable=True),
        sa.Column('venue_data', sa.Text(), nullable=True),
        sa.Column('rec_ids', sa.Text(), nullable=True),
        sa.Column('gift_rec_ids', sa.Text(), nullable=True),
        sa.Column('pending_save', sa.Text(), nullable=True),
        sa.Column('booking_id', sa.String(), nullable=True),
        sa.Column('ai_fallback_venues', sa.Text(), nullable=True),
        sa.Column('ai_fallback_gifts', sa.Text(), nullable=True),
        sa.Column('is_ai_fallback', sa.String(), nullable=True, server_default='false'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_chat_sessions_event_id'), 'chat_sessions', ['event_id'], unique=True)
    op.create_index(op.f('ix_chat_sessions_id'), 'chat_sessions', ['id'], unique=False)
