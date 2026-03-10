"""baseline schema

Revision ID: 20260306_0001
Revises:
Create Date: 2026-03-06 00:01:00
"""

from alembic import op

from src.models.base import Base
from src.models.category import Category, ProductCategory
from src.models.collection import Collection, CollectionImage, CollectionProduct
from src.models.orders import Order, OrderProduct
from src.models.product import Product, ProductColor, ProductImage, ProductSection, ProductSize
from src.models.promocode import PromoCode
from src.models.site_settings import SiteSetting
from src.models.user import User

# revision identifiers, used by Alembic.
revision = "20260306_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
