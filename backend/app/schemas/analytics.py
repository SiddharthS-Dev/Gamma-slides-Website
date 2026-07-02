"""Analytics response schemas."""

from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel


class TrendingItem(BaseModel):
    """Trending presentation."""
    id: UUID
    title: str
    thumbnail_url: Optional[str] = None
    view_count: int
    trend_score: float
    file_type: str
    created_at: Optional[datetime] = None


class AnalyticsSummary(BaseModel):
    """Dashboard analytics summary."""
    total_presentations: int
    total_views: int
    total_downloads: int
    total_categories: int
    total_tags: int
    total_storage_bytes: int
    trending: list[TrendingItem] = []
    most_viewed: list[TrendingItem] = []
    recently_added: list[TrendingItem] = []


class SearchStats(BaseModel):
    """Search analytics."""
    total_searches: int
    unique_queries: int
    top_queries: list[dict] = []
    zero_result_queries: list[str] = []


class StorageStats(BaseModel):
    """Storage monitoring stats."""
    total_files: int
    total_size_bytes: int
    by_type: dict[str, dict] = {}
    thumbnail_count: int
    thumbnail_size_bytes: int


class IngestionStatus(BaseModel):
    """Ingestion engine status."""
    is_running: bool
    last_scan_at: Optional[datetime] = None
    files_processed: int
    files_failed: int
    files_skipped: int
    watch_paths: list[str] = []
