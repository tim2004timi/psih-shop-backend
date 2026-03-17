"""add price and discount_price to product_colors

Revision ID: 20260318_0005
Revises: 20260317_0004
Create Date: 2026-03-18 00:05:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260318_0005"
down_revision = "20260317_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("product_colors", sa.Column("price", sa.Numeric(10, 2), nullable=True))
    op.add_column("product_colors", sa.Column("discount_price", sa.Numeric(10, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("product_colors", "discount_price")
    op.drop_column("product_colors", "price")
