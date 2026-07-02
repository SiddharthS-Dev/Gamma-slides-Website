"""Search request/response schemas."""

from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.presentation import PresentationListItem


class SearchRequest(BaseModel):
    """Search query parameters."""
    q: str = Field(..., min_length=1, max_length=500)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=24, ge=1, le=100)
    category_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    file_type: Optional[str] = None
    author: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: str = "relevance"  # relevance, title, created_at, popularity_score


class SearchResultItem(PresentationListItem):
    """Search result with ranking info."""
    headline: Optional[str] = None  # Highlighted search match
    rank: float = 0.0


class SearchResponse(BaseModel):
    """Paginated search results."""
    items: list[SearchResultItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    query: str
    suggestions: list[str] = Field(default_factory=list)


class SearchSuggestion(BaseModel):
    """Auto-complete suggestion."""
    text: str
    type: str = "title"  # title, tag, category, author


class SearchHistoryItem(BaseModel):
    """Recent search entry."""
    query: str
    result_count: Optional[int] = None
    searched_at: datetime

    model_config = {"from_attributes": True}
