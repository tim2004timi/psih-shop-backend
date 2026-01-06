from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from src.models.product import ProductStatus

class ProductSectionBase(BaseModel):
    title: str = Field(..., max_length=200, description="Заголовок аккордеона")
    content: str = Field(..., description="Содержимое аккордеона")
    sort_order: int = Field(default=0, description="Порядок сортировки")

class ProductSectionCreate(ProductSectionBase):
    pass

class ProductSectionUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None
    sort_order: Optional[int] = None

class ProductSectionOut(ProductSectionBase):
    id: int
    product_id: int

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    description: Optional[str] = Field(None, description="Описание продукта")
    price: Decimal = Field(..., decimal_places=2, gt=0, description="Цена продукта (должна быть больше 0)")
    discount_price: Optional[Decimal] = Field(None, decimal_places=2, gt=0, description="Цена со скидкой (должна быть больше 0)")
    weight: float = Field(..., gt=0, description="Вес продукта в КГ (например, 0.5)")
    currency: str = Field(default="RUB", max_length=3, description="Валюта")
    composition: Optional[str] = Field(None, max_length=200, description="Состав продукта")
    fit: Optional[str] = Field(None, max_length=50, description="Посадка/размер")
    status: ProductStatus = Field(default=ProductStatus.IN_STOCK, description="Статус продукта")
    is_pre_order: bool = Field(default=False, description="Доступен ли для предзаказа")
    meta_care: Optional[str] = Field(None, max_length=200, description="Инструкции по уходу")
    meta_shipping: Optional[str] = Field(None, max_length=100, description="Информация о доставке")
    meta_returns: Optional[str] = Field(None, max_length=100, description="Информация о возврате")

class ProductCreate(ProductBase):
    pass  # id будет генерироваться автоматически

class ProductUpdate(BaseModel):
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, decimal_places=2, gt=0)
    discount_price: Optional[Decimal] = Field(None, decimal_places=2, gt=0)
    weight: Optional[float] = Field(None, gt=0, description="Вес продукта в КГ (например, 0.5)")
    currency: Optional[str] = Field(None, max_length=3)
    composition: Optional[str] = Field(None, max_length=200)
    fit: Optional[str] = Field(None, max_length=50)
    status: Optional[ProductStatus] = None
    is_pre_order: Optional[bool] = None
    meta_care: Optional[str] = Field(None, max_length=200)
    meta_shipping: Optional[str] = Field(None, max_length=100)
    meta_returns: Optional[str] = Field(None, max_length=100)

class ProductInDB(ProductBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ProductColorBase(BaseModel):
    slug: str = Field(..., max_length=100, description="Уникальный slug для продукта с цветом")
    title: str = Field(..., max_length=200, description="Название продукта")
    label: str = Field(..., max_length=100, description="Название цвета")
    hex: str = Field(..., max_length=7, description="HEX код цвета")

class ProductColorCreate(ProductColorBase):
    product_id: int

class ProductColorUpdate(BaseModel):
    slug: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=200)
    label: Optional[str] = Field(None, max_length=100)
    hex: Optional[str] = Field(None, max_length=7)

class ProductColorOut(ProductColorBase):
    id: int
    product_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ProductColorIn(BaseModel):
    slug: str
    title: str
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

class MainCategory(BaseModel):
    name: str
    slug: str

class ProductPublic(BaseModel):
    id: int  # ID базового продукта
    color_id: int  # ID цвета продукта
    slug: str
    title: str
    categoryPath: List[str] = Field(default_factory=list)
    main_category: Optional[MainCategory] = None
    price: Decimal
    discount_price: Optional[Decimal] = None
    currency: str
    weight: float  # Вес продукта
    label: str  # название цвета
    hex: str  # HEX код цвета
    sizes: List[dict] = Field(default_factory=list)  # список размеров с количеством
    composition: Optional[str] = None
    fit: Optional[str] = None
    description: Optional[str] = None
    images: List[ProductImageOut] = Field(default_factory=list)
    meta: ProductMeta
    status: ProductStatus
    custom_sections: List[ProductSectionOut] = Field(default_factory=list)

    class Config:
        from_attributes = True

class ProductSizeBase(BaseModel):
    size: str = Field(..., max_length=10, description="Размер")
    quantity: int = Field(..., ge=0, description="Количество")

class ProductSizeCreate(ProductSizeBase):
    product_color_id: int

class ProductSizeUpdate(BaseModel):
    size: Optional[str] = Field(None, max_length=10)
    quantity: Optional[int] = Field(None, ge=0)

class ProductSizeOut(ProductSizeBase):
    id: int
    product_color_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ProductSizeIn(BaseModel):
    size: str
    quantity: int = Field(default=0, ge=0, description="Количество (должно быть >= 0)")

class ProductList(BaseModel):
    products: list[ProductPublic]
    total: int
    skip: int
    limit: int

class ProductColorDetail(BaseModel):
    """Детальная информация о цвете продукта"""
    id: int  # Добавлено для фронтенда
    color_id: int
    slug: str
    title: str
    label: str
    hex: str
    images: List[ProductImageOut] = Field(default_factory=list)
    sizes: List[dict] = Field(default_factory=list)  # список размеров с количеством

class ProductDetail(BaseModel):
    """Детальная информация о продукте со всеми цветами"""
    id: int
    description: Optional[str] = None
    price: Decimal
    discount_price: Optional[Decimal] = None
    currency: str
    weight: float  # Вес продукта
    composition: Optional[str] = None
    fit: Optional[str] = None
    status: ProductStatus
    is_pre_order: bool
    main_category: Optional[MainCategory] = None
    meta_care: Optional[str] = None
    meta_shipping: Optional[str] = None
    meta_returns: Optional[str] = None
    colors: List[ProductColorDetail] = Field(default_factory=list)
    custom_sections: List[ProductSectionOut] = Field(default_factory=list)

    class Config:
        from_attributes = True
