"""Category, Department, and Tag schemas."""

from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel


class CategoryCreate(BaseModel):
    """Create a new category."""
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#6366f1"
    icon: Optional[str] = "folder"
    sort_order: int = 0


class CategoryResponse(BaseModel):
    """Category response."""
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    presentation_count: int = 0
    parent_id: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DepartmentCreate(BaseModel):
    """Create a new department."""
    name: str
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    sort_order: int = 0


class DepartmentResponse(BaseModel):
    """Department response with optional children."""
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    sort_order: int = 0
    created_at: datetime
    children: list["DepartmentResponse"] = []

    model_config = {"from_attributes": True}


class TagCreate(BaseModel):
    """Create a new tag."""
    name: str
    color: Optional[str] = "#8b5cf6"


class TagResponse(BaseModel):
    """Tag response."""
    id: UUID
    name: str
    slug: str
    color: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TagPopular(BaseModel):
    """Popular tag with usage count."""
    id: UUID
    name: str
    slug: str
    color: Optional[str] = None
    count: int = 0

    model_config = {"from_attributes": True}
