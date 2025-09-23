from sqlalchemy import Column, String, DateTime, func, Boolean, Integer, ForeignKey
from src.models.base import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    parent_id = Column(String(36), ForeignKey("categories.id"), nullable=True, index=True)
    level = Column(Integer, default=0)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class ProductCategory(Base):
    __tablename__ = "product_categories"

    product_id = Column(String(50), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    category_id = Column(String(36), ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True, index=True)


