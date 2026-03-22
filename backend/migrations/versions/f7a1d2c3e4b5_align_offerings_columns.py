"""align offerings columns

Revision ID: f7a1d2c3e4b5
Revises: f6b8c3d1a9e0
Create Date: 2026-03-23 00:20:00
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "f7a1d2c3e4b5"
down_revision = "f6b8c3d1a9e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE offerings ADD COLUMN IF NOT EXISTS quality_tier VARCHAR NOT NULL DEFAULT 'MEDIUM'")
    op.execute("ALTER TABLE offerings ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now()")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_offerings_vendor_id_vendors'
            ) THEN
                ALTER TABLE offerings
                ADD CONSTRAINT fk_offerings_vendor_id_vendors
                FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id);
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE offerings DROP CONSTRAINT IF EXISTS fk_offerings_vendor_id_vendors")
    op.execute("ALTER TABLE offerings DROP COLUMN IF EXISTS created_at")
    op.execute("ALTER TABLE offerings DROP COLUMN IF EXISTS quality_tier")
