from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
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

class ProductResponse(ProductInDB):
    pass

class ProductList(BaseModel):
    products: list[ProductResponse]
    total: int
    skip: int
    limit: int
