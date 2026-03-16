"""add size_chart to products table

Revision ID: 20260317_0004
Revises: 20260306_0003
Create Date: 2026-03-17 12:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260317_0004"
down_revision = "20260306_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS size_chart TEXT")
    else:
        op.add_column("products", sa.Column("size_chart", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("products", "size_chart")
