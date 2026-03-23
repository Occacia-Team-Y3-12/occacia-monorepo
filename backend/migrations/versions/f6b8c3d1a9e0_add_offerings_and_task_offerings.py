"""add offerings and task_offerings

Revision ID: f6b8c3d1a9e0
Revises: 2b4842561c90, c2f1a6e8d9b0, d4e5f6a7b8c9
Create Date: 2026-03-23 00:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f6b8c3d1a9e0"
down_revision = ("2b4842561c90", "c2f1a6e8d9b0", "d4e5f6a7b8c9")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "offerings",
        sa.Column("quality_tier", sa.String(), server_default="MEDIUM", nullable=False),
    )
    op.add_column(
        "offerings",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_foreign_key(
        "fk_offerings_vendor_id_vendors",
        "offerings",
        "vendors",
        ["vendor_id"],
        ["vendor_id"],
    )

    op.create_table(
        "task_offerings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("offering_id", sa.String(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("is_selected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("selected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["offering_id"], ["offerings.offering_id"]),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.task_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_offerings_id"), "task_offerings", ["id"], unique=False)
    op.create_index(op.f("ix_task_offerings_offering_id"), "task_offerings", ["offering_id"], unique=False)
    op.create_index(op.f("ix_task_offerings_task_id"), "task_offerings", ["task_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_task_offerings_task_id"), table_name="task_offerings")
    op.drop_index(op.f("ix_task_offerings_offering_id"), table_name="task_offerings")
    op.drop_index(op.f("ix_task_offerings_id"), table_name="task_offerings")
    op.drop_table("task_offerings")

    op.drop_constraint("fk_offerings_vendor_id_vendors", "offerings", type_="foreignkey")
    op.drop_column("offerings", "created_at")
    op.drop_column("offerings", "quality_tier")
