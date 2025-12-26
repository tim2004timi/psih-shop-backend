from pydantic import BaseModel, Field
from typing import List, Optional


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

