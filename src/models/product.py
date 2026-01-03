from sqlalchemy import Column, String, Text, Numeric, Boolean, DateTime, func, Enum, ForeignKey, Integer, CheckConstraint
from sqlalchemy.orm import declarative_base, relationship
from src.models.base import Base
import enum

class ProductStatus(str, enum.Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    discount_price = Column(Numeric(10, 2), nullable=True)
    weight = Column(Integer, nullable=False) # weight in grams
    currency = Column(String(3), default="RUB")
    composition = Column(String(200), nullable=True)
    fit = Column(String(50), nullable=True)
    status = Column(Enum(ProductStatus), default=ProductStatus.IN_STOCK)
    is_pre_order = Column(Boolean, default=False)
    meta_care = Column(String(200), nullable=True)
    meta_shipping = Column(String(100), nullable=True)
    meta_returns = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint('price > 0', name='check_price_positive'),
        CheckConstraint('discount_price IS NULL OR discount_price > 0', name='check_discount_price_positive'),
        CheckConstraint('weight > 0', name='check_weight_positive'),
    )

    def __repr__(self):
        return f"<Product(id={self.id}, price={self.price})>"


class ProductColor(Base):
    __tablename__ = "product_colors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    slug = Column(String(100), unique=True, index=True, nullable=False)  # slug продукта с цветом
    title = Column(String(200), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(100), nullable=False)  # название цвета
    hex = Column(String(7), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class ProductSize(Base):
    __tablename__ = "product_sizes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_color_id = Column(Integer, ForeignKey("product_colors.id", ondelete="CASCADE"), nullable=False, index=True)
    size = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint('quantity >= 0', name='check_product_size_quantity_non_negative'),
    )


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_color_id = Column(Integer, ForeignKey("product_colors.id", ondelete="CASCADE"), nullable=False, index=True)
    file = Column(String(200), nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
