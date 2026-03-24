"""add payment_provider to orders

Revision ID: 20260323_0006
Revises: 20260318_0005
Create Date: 2026-03-23 00:06:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260323_0006"
down_revision = "20260318_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("payment_provider", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "payment_provider")
