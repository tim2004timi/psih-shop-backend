from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal
from src.models.promocode import DiscountType


class PromoCodeCreate(BaseModel):
    code: str = Field(..., max_length=50)
    discount_type: DiscountType
    discount_value: Decimal = Field(..., gt=0)
    description: Optional[str] = Field(default="", max_length=255)
    max_uses: Optional[int] = Field(default=None, ge=1)
    expires_at: Optional[datetime] = None


class PromoCodeUpdate(BaseModel):
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[Decimal] = Field(default=None, gt=0)
    description: Optional[str] = Field(default=None, max_length=255)
    max_uses: Optional[int] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class PromoCodeResponse(BaseModel):
    id: int
    code: str
    discount_type: DiscountType
    discount_value: Decimal
    description: Optional[str]
    max_uses: Optional[int]
    used_count: int
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class PromoCodeValidateRequest(BaseModel):
    code: str
    order_amount: Decimal = Field(..., gt=0)


class PromoCodeValidateResponse(BaseModel):
    valid: bool
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    message: str
