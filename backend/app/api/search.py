"""Search API routes."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.presentation import Presentation
from app.services import search_service
from app.schemas.search import SearchResponse, SearchSuggestion, SearchHistoryItem

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=SearchResponse)
async def search_presentations(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    category_id: Optional[UUID] = None,
    department_id: Optional[UUID] = None,
    file_type: Optional[str] = None,
    author: Optional[str] = None,
    sort_by: str = Query(default="relevance"),
    session_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Full-text search with fuzzy matching, filtering, and ranking."""
    return await search_service.search_presentations(
        db=db,
        query_str=q,
        page=page,
        page_size=page_size,
        category_id=category_id,
        department_id=department_id,
        file_type=file_type,
        author=author,
        sort_by=sort_by,
        session_id=session_id,
    )


@router.get("/suggestions", response_model=list[SearchSuggestion])
async def get_suggestions(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Get auto-complete suggestions for search."""
    return await search_service.get_search_suggestions(db, q, limit)


@router.get("/history", response_model=list[SearchHistoryItem])
async def get_search_history(
    session_id: Optional[str] = None,
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get recent search history."""
    return await search_service.get_search_history(db, session_id, limit)


@router.get("/sync/version")
async def sync_version(db: AsyncSession = Depends(get_db)):
    """Return the current sync version so clients can detect new presentations.

    The frontend polls this endpoint every 5 minutes and refreshes its IndexedDB
    cache when the count or updated_at timestamp has changed.
    """
    result = await db.execute(
        select(
            func.count(Presentation.id).label("count"),
            func.max(Presentation.updated_at).label("updated_at"),
        ).where(Presentation.is_active == True)  # noqa: E712
    )
    row = result.one()
    return {
        "version": row.count,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }
