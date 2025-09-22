from sqlalchemy import Column, String, Text, Numeric, Boolean, DateTime, func, Enum
from sqlalchemy.orm import declarative_base
from src.models.base import Base
import enum

class ProductStatus(str, enum.Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"

class Product(Base):
    __tablename__ = "products"

    id = Column(String(50), primary_key=True, index=True)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="EUR")
    composition = Column(String(200), nullable=True)
    fit = Column(String(50), nullable=True)
    status = Column(Enum(ProductStatus), default=ProductStatus.IN_STOCK)
    is_pre_order = Column(Boolean, default=False)
    meta_care = Column(String(200), nullable=True)
    meta_shipping = Column(String(100), nullable=True)
    meta_returns = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Product(id={self.id}, title={self.title}, price={self.price})>"
