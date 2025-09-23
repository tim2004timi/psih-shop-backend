from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from src.models.product import ProductStatus

class ProductBase(BaseModel):
    slug: str = Field(..., max_length=100, description="Уникальный slug для продукта")
    title: str = Field(..., max_length=200, description="Название продукта")
    description: Optional[str] = Field(None, description="Описание продукта")
    price: Decimal = Field(..., decimal_places=2, description="Цена продукта")
    currency: str = Field(default="EUR", max_length=3, description="Валюта")
    composition: Optional[str] = Field(None, max_length=200, description="Состав продукта")
    fit: Optional[str] = Field(None, max_length=50, description="Посадка/размер")
    status: ProductStatus = Field(default=ProductStatus.IN_STOCK, description="Статус продукта")
    is_pre_order: bool = Field(default=False, description="Доступен ли для предзаказа")
    meta_care: Optional[str] = Field(None, max_length=200, description="Инструкции по уходу")
    meta_shipping: Optional[str] = Field(None, max_length=100, description="Информация о доставке")
    meta_returns: Optional[str] = Field(None, max_length=100, description="Информация о возврате")

class ProductCreate(ProductBase):
    id: str = Field(..., max_length=50, description="Уникальный ID продукта")

class ProductUpdate(BaseModel):
    slug: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, decimal_places=2)
    currency: Optional[str] = Field(None, max_length=3)
    composition: Optional[str] = Field(None, max_length=200)
    fit: Optional[str] = Field(None, max_length=50)
    status: Optional[ProductStatus] = None
    is_pre_order: Optional[bool] = None
    meta_care: Optional[str] = Field(None, max_length=200)
    meta_shipping: Optional[str] = Field(None, max_length=100)
    meta_returns: Optional[str] = Field(None, max_length=100)

class ProductInDB(ProductBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProductColorOut(BaseModel):
    code: str
    label: str
    hex: str

class ProductColorIn(BaseModel):
    id: str
    code: str
    label: str
    hex: str

class ProductImageOut(BaseModel):
    file: str
    alt: Optional[str] = None
    w: Optional[int] = None
    h: Optional[int] = None
    color: Optional[str] = None

class ProductMeta(BaseModel):
    care: Optional[str] = None
    shipping: Optional[str] = None
    returns: Optional[str] = None

class ProductPublic(BaseModel):
    id: str
    slug: str
    title: str
    categoryPath: List[str] = Field(default_factory=list)
    price: Decimal
    currency: str
    colors: List[ProductColorOut] = Field(default_factory=list)
    sizes: List[str] = Field(default_factory=list)
    composition: Optional[str] = None
    fit: Optional[str] = None
    description: Optional[str] = None
    images: List[ProductImageOut] = Field(default_factory=list)
    meta: ProductMeta
    status: ProductStatus

class ProductSizeIn(BaseModel):
    id: str
    size: str

class ProductList(BaseModel):
    products: list[ProductPublic]
    total: int
    skip: int
    limit: int
