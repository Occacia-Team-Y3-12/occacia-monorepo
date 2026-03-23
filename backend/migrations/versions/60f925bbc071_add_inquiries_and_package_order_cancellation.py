"""add inquiries and package order cancellation

Revision ID: 60f925bbc071
Revises: f7a1d2c3e4b5
Create Date: 2026-03-23 00:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "60f925bbc071"
down_revision = "f7a1d2c3e4b5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inquiries",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("inquiry_id", sa.String(), nullable=False),
        sa.Column("created_by_user_id", sa.String(), nullable=False),
        sa.Column("created_by_role", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="OPEN"),
        sa.Column("handled_by_admin_id", sa.String(), nullable=True),
        sa.Column("admin_reply", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_inquiries_id"), "inquiries", ["id"], unique=False)
    op.create_index(op.f("ix_inquiries_inquiry_id"), "inquiries", ["inquiry_id"], unique=True)
    op.create_index(op.f("ix_inquiries_created_by_user_id"), "inquiries", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_inquiries_status"), "inquiries", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_inquiries_status"), table_name="inquiries")
    op.drop_index(op.f("ix_inquiries_created_by_user_id"), table_name="inquiries")
    op.drop_index(op.f("ix_inquiries_inquiry_id"), table_name="inquiries")
    op.drop_index(op.f("ix_inquiries_id"), table_name="inquiries")
    op.drop_table("inquiries")
