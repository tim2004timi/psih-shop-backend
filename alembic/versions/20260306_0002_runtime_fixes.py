"""runtime fixes and guest access token

Revision ID: 20260306_0002
Revises: 20260306_0001
Create Date: 2026-03-06 00:02:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260306_0002"
down_revision = "20260306_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute("ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0")
        op.execute("ALTER TABLE product_sizes ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0")
        op.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS access_token VARCHAR(64)")
        op.execute("UPDATE orders SET access_token = md5(random()::text || clock_timestamp()::text) WHERE access_token IS NULL")
        op.execute("ALTER TABLE orders ALTER COLUMN access_token SET NOT NULL")
        op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_orders_access_token ON orders (access_token)")
        op.execute("DROP INDEX IF EXISTS ix_product_colors_slug")
        op.execute("CREATE INDEX IF NOT EXISTS ix_product_colors_slug ON product_colors (slug)")
        return

    inspector = sa.inspect(bind)
    order_columns = {column["name"] for column in inspector.get_columns("orders")}
    if "access_token" not in order_columns:
        op.add_column("orders", sa.Column("access_token", sa.String(length=64), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_orders_access_token")
        op.execute("ALTER TABLE orders DROP COLUMN IF EXISTS access_token")
        return

    inspector = sa.inspect(bind)
    order_columns = {column["name"] for column in inspector.get_columns("orders")}
    if "access_token" in order_columns:
        op.drop_column("orders", "access_token")
