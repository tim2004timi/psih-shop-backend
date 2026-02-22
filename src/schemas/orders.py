from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from src.models.orders import OrderStatus, DeliveryMethod

class OrderBase(BaseModel):
    email: str = Field(..., max_length=100, description="Email покупателя")
    first_name: str = Field(..., max_length=50, description="Имя покупателя")
    last_name: str = Field(..., max_length=50, description="Фамилия покупателя")
    phone: Optional[str] = Field(None, max_length=15, description="Телефон покупателя")
    city: Optional[str] = Field(None, max_length=255, description="Город доставки")
    postal_code: Optional[str] = Field(None, max_length=10, description="Почтовый индекс")
    address: Optional[str] = Field(None, max_length=200, description="Адрес доставки")
    status: OrderStatus = Field(default=OrderStatus.NOT_PAID, description="Статус заказа")

class OrderCreate(OrderBase):
    user_id: Optional[int] = Field(None, description="ID пользователя (если заказ от авторизованного пользователя)")
    # total_price будет вычисляться автоматически на основе товаров

class OrderProductBase(BaseModel):
    product_size_id: int = Field(..., description="ID размера продукта")
    quantity: int = Field(..., gt=0, description="Количество товара (должно быть больше 0)")

class OrderProductCreate(OrderProductBase):
    pass  # order_id будет установлен автоматически при создании заказа

class OrderCreateRequest(BaseModel):
    """Схема для создания заказа с товарами"""
    order: OrderCreate
    products: List[OrderProductCreate] = Field(..., min_items=1, description="Список товаров в заказе")

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None

class OrderInDB(OrderBase):
    id: int
    total_price: Decimal = Field(..., decimal_places=2, gt=0, description="Общая стоимость заказа (должна быть больше 0)")
    delivery_method: DeliveryMethod = Field(..., description="Способ доставки")
    cdek_status: Optional[str] = Field(None, description="Статус заказа в CDEK")
    user_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

class OrderProductInDB(OrderProductBase):
    id: int
    order_id: int

    class Config:
        from_attributes = True

class OrderProductDetail(BaseModel):
    """Детальная информация о товаре в заказе"""
    id: int
    product_id: int
    product_color_id: int
    slug: str
    title: str
    label: str
    hex: str
    price: Decimal
    discount_price: Optional[Decimal]
    currency: str
    size: str
    quantity: int

    class Config:
        from_attributes = True

class OrderDetail(BaseModel):
    """Полная информация о заказе с товарами"""
    id: int
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    city: Optional[str]
    postal_code: Optional[str]
    address: Optional[str]
    total_price: Decimal
    delivery_method: DeliveryMethod
    status: OrderStatus
    cdek_status: Optional[str]
    user_id: Optional[int]
    cdek_uuid: Optional[str] = None
    cdek_number: Optional[str] = None
    created_at: datetime
    products: List[OrderProductDetail] = Field(default_factory=list)

    class Config:
        from_attributes = True
