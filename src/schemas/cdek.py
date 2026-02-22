from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class CDEKCity(BaseModel):
    """Схема для города из CDEK API"""
    city_uuid: str = Field(..., description="UUID города в системе CDEK")
    code: int = Field(..., description="Код города")
    full_name: str = Field(..., description="Полное название города")
    country_code: str = Field(..., description="Код страны")

    class Config:
        from_attributes = True


class CDEKOffice(BaseModel):
    """Схема для пункта выдачи (офиса) из CDEK API"""
    code: str = Field(..., description="Код пункта выдачи")
    uuid: str = Field(..., description="UUID пункта выдачи")
    type: str = Field(..., description="Тип пункта выдачи (например, PVZ)")
    work_time: Optional[str] = Field(None, description="Время работы пункта выдачи")
    city_code: int = Field(..., description="Код города")
    city: str = Field(..., description="Название города")
    longitude: float = Field(..., description="Долгота")
    latitude: float = Field(..., description="Широта")
    address: str = Field(..., description="Адрес пункта выдачи")

    class Config:
        from_attributes = True


class CDEKOfficeList(BaseModel):
    """Список пунктов выдачи из CDEK"""
    offices: List[CDEKOffice] = Field(..., description="Список пунктов выдачи")

class CDEKOrderUpdate(BaseModel):
    """Schema for updating a CDEK order (type=1)"""
    type: int = Field(1, description="Order type (1 - ��������-�������)")
    number: Optional[str] = Field(None, description="Client order number")
    tariff_code: Optional[int] = Field(None, description="Tariff code")
    comment: Optional[str] = Field(None, description="Order comment")
    shipment_point: Optional[str] = Field(None, description="CDEK pickup point (from warehouse)")
    delivery_point: Optional[str] = Field(None, description="CDEK pickup point (to warehouse)")
    recipient: Optional[Dict[str, Any]] = Field(None, description="Recipient")
