from pydantic import BaseModel
from typing import Optional, List


class CategoryCreate(BaseModel):
    name: str
    slug: str
    parent_id: Optional[int] = None
    level: int = 0
    sort_order: int = 0
    is_active: bool = True


class CategoryNode(BaseModel):
    id: int
    name: str
    slug: str
    children: List["CategoryNode"] = []

    class Config:
        arbitrary_types_allowed = True
        json_schema_extra = {
            "$defs": {
                "CategoryNode": {}
            }
        }


