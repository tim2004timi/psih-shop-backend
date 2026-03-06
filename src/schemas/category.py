from pydantic import BaseModel, ConfigDict, Field
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
    children: List["CategoryNode"] = Field(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)


CategoryNode.model_rebuild()


