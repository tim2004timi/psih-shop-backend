from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime

class SiteSettingBase(BaseModel):
    key: str
    value: str # JSON string

class SiteSettingUpdate(BaseModel):
    value: str # JSON string

class SiteSettingPublic(SiteSettingBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True

