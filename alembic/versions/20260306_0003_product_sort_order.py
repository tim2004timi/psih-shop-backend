"""add sort_order to products table

Revision ID: 20260306_0003
Revises: 20260306_0002
Create Date: 2026-03-06 12:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260306_0003"
down_revision = "20260306_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0")
        op.execute("UPDATE products SET sort_order = id WHERE sort_order = 0")
    else:
        op.add_column("products", sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("products", "sort_order")
