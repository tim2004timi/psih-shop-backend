from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from src.models.collection import CollectionCategory


class CollectionBase(BaseModel):
    name: str = Field(..., max_length=100)
    slug: str = Field(..., max_length=100)
    season: str = Field(..., max_length=20)
    year: int
    description: Optional[str] = None
    story: Optional[str] = None
    inspiration: Optional[str] = None
    key_pieces: Optional[List[str]] = None
    sustainability: Optional[str] = None
    is_new: bool = Field(default=True)
    is_featured: bool = Field(default=False)
    category: CollectionCategory = Field(default=CollectionCategory.UNISEX)


class CollectionCreate(CollectionBase):
    id: str = Field(..., max_length=50)


class CollectionUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    slug: Optional[str] = Field(None, max_length=100)
    season: Optional[str] = Field(None, max_length=20)
    year: Optional[int] = None
    description: Optional[str] = None
    story: Optional[str] = None
    inspiration: Optional[str] = None
    key_pieces: Optional[List[str]] = None
    sustainability: Optional[str] = None
    is_new: Optional[bool] = None
    is_featured: Optional[bool] = None
    category: Optional[CollectionCategory] = None


class CollectionImageOut(BaseModel):
    id: str
    file: str
    sort_order: int


class CollectionResponse(CollectionBase):
    id: str
    created_at: str
    images: List[CollectionImageOut] = Field(default_factory=list)


class CollectionListResponse(BaseModel):
    collections: List[CollectionResponse]
    total: int
    skip: int
    limit: int


class CollectionImageIn(BaseModel):
    id: str
    sort_order: int = 0


class CollectionProductIn(BaseModel):
    product_id: str
    sort_order: int = 0
