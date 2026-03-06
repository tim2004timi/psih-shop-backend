from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)

