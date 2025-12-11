from sqlalchemy import Column, String, DateTime, func, Boolean, Integer, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import ENUM
from src.models.base import Base
import enum


class CollectionCategory(str, enum.Enum):
    MEN = "men"
    WOMEN = "women"
    UNISEX = "unisex"


class Collection(Base):
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    season = Column(String(20), nullable=False)
    year = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    story = Column(Text, nullable=True)
    inspiration = Column(Text, nullable=True)
    key_pieces = Column(JSON, nullable=True)
    sustainability = Column(Text, nullable=True)
    is_new = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    category = Column(ENUM(CollectionCategory), default=CollectionCategory.UNISEX)
    created_at = Column(DateTime, server_default=func.now())


class CollectionImage(Base):
    __tablename__ = "collection_images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    collection_id = Column(Integer, ForeignKey("collections.id", ondelete="CASCADE"), nullable=False, index=True)
    file = Column(String(200), nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class CollectionProduct(Base):
    __tablename__ = "collection_products"

    collection_id = Column(Integer, ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), primary_key=True, index=True)
    sort_order = Column(Integer, default=0)
