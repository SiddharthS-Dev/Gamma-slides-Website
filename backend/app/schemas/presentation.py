"""Presentation request/response schemas."""

from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field


class CategoryBrief(BaseModel):
    """Minimal category info embedded in presentation responses."""
    id: UUID
    name: str
    color: Optional[str] = None

    model_config = {"from_attributes": True}


class DepartmentBrief(BaseModel):
    """Minimal department info embedded in presentation responses."""
    id: UUID
    name: str

    model_config = {"from_attributes": True}


class TagBrief(BaseModel):
    """Minimal tag info embedded in presentation responses."""
    id: UUID
    name: str
    color: Optional[str] = None

    model_config = {"from_attributes": True}


class PresentationListItem(BaseModel):
    """Single presentation in list/grid view."""
    id: UUID
    title: str
    description: Optional[str] = None
    file_name: str
    file_type: str
    file_size: int
    slide_count: Optional[int] = None
    reading_time_minutes: Optional[int] = None
    thumbnail_url: Optional[str] = None
    category: Optional[CategoryBrief] = None
    department: Optional[DepartmentBrief] = None
    tags: list[TagBrief] = Field(default_factory=list)
    author: Optional[str] = None
    version: Optional[str] = None
    view_count: int = 0
    download_count: int = 0
    popularity_score: float = 0.0
    created_at: datetime
    updated_at: datetime
    is_offline_available: bool = False

    model_config = {"from_attributes": True}


class PresentationDetail(PresentationListItem):
    """Full presentation detail for the viewer page."""
    file_path: str
    file_hash: str
    file_modified_at: Optional[datetime] = None
    last_viewed_at: Optional[datetime] = None
    is_active: bool = True


class PresentationPage(BaseModel):
    """Paginated list of presentations."""
    items: list[PresentationListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class PresentationUpdate(BaseModel):
    """Schema for updating presentation metadata."""
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    author: Optional[str] = None
    version: Optional[str] = None
    tag_ids: Optional[list[UUID]] = None


class ViewEvent(BaseModel):
    """Schema for recording a view event."""
    session_id: Optional[str] = None
    slide_number: Optional[int] = None
    duration_seconds: Optional[int] = None


class BookmarkCreate(BaseModel):
    """Schema for creating a bookmark."""
    slide_number: Optional[int] = None
    note: Optional[str] = None
    session_id: Optional[str] = None


class BookmarkResponse(BaseModel):
    """Bookmark response."""
    id: UUID
    presentation_id: UUID
    slide_number: Optional[int] = None
    note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
