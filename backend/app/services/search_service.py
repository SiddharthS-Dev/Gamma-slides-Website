"""Search service — full-text search with fuzzy matching and suggestions."""

import math
from uuid import UUID
from typing import Optional
from datetime import datetime

from sqlalchemy import select, func, text, desc, literal_column
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.presentation import Presentation
from app.models.analytics import SearchHistory
from app.schemas.presentation import CategoryBrief, DepartmentBrief, TagBrief
from app.schemas.search import (
    SearchResultItem, SearchResponse, SearchSuggestion, SearchHistoryItem,
)
from app.config import get_settings

settings = get_settings()


async def search_presentations(
    db: AsyncSession,
    query_str: str,
    page: int = 1,
    page_size: int = 24,
    category_id: Optional[UUID] = None,
    department_id: Optional[UUID] = None,
    file_type: Optional[str] = None,
    author: Optional[str] = None,
    sort_by: str = "relevance",
    session_id: Optional[str] = None,
) -> SearchResponse:
    """Full-text search with fuzzy matching using PostgreSQL ts_vector + pg_trgm."""

    # Build the search query using plainto_tsquery for robustness
    search_query = text("""
        SELECT
            p.*,
            ts_rank(p.search_vector, plainto_tsquery('english', :q)) AS rank,
            ts_headline('english', p.title || ' ' || COALESCE(p.description, ''),
                        plainto_tsquery('english', :q),
                        'StartSel=<mark>, StopSel=</mark>, MaxWords=50, MinWords=20'
            ) AS headline
        FROM presentations p
        WHERE p.is_active = true
          AND (
            p.search_vector @@ plainto_tsquery('english', :q)
            OR similarity(p.title, :q) > :threshold
          )
    """)

    params = {
        "q": query_str,
        "threshold": settings.fuzzy_threshold,
    }

    # Build filter clauses
    filter_clauses = []
    if category_id:
        filter_clauses.append(f"AND p.category_id = '{category_id}'")
    if department_id:
        filter_clauses.append(f"AND p.department_id = '{department_id}'")
    if file_type:
        filter_clauses.append(f"AND p.file_type = '{file_type.lower()}'")

    filters_sql = " ".join(filter_clauses)

    # Build sort clause
    if sort_by == "title":
        order_clause = "ORDER BY p.title ASC"
    elif sort_by == "created_at":
        order_clause = "ORDER BY p.created_at DESC"
    elif sort_by == "popularity_score":
        order_clause = "ORDER BY p.popularity_score DESC"
    else:  # relevance
        order_clause = "ORDER BY rank DESC, similarity(p.title, :q) DESC"

    offset = (page - 1) * page_size

    # Full query with count
    full_sql = text(f"""
        WITH search_results AS (
            SELECT
                p.*,
                ts_rank(p.search_vector, plainto_tsquery('english', :q)) AS rank,
                ts_headline('english', p.title || ' ' || COALESCE(p.description, ''),
                            plainto_tsquery('english', :q),
                            'StartSel=<mark>, StopSel=</mark>, MaxWords=50, MinWords=20'
                ) AS headline
            FROM presentations p
            WHERE p.is_active = true
              AND (
                p.search_vector @@ plainto_tsquery('english', :q)
                OR similarity(p.title, :q) > :threshold
              )
              {filters_sql}
        )
        SELECT *, (SELECT COUNT(*) FROM search_results) AS total_count
        FROM search_results
        {order_clause}
        LIMIT :limit OFFSET :offset
    """)

    params["limit"] = page_size
    params["offset"] = offset

    result = await db.execute(full_sql, params)
    rows = result.mappings().all()

    total = rows[0]["total_count"] if rows else 0
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    items = []
    for row in rows:
        items.append(SearchResultItem(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            file_name=row["file_name"],
            file_type=row["file_type"],
            file_size=row["file_size"],
            slide_count=row["slide_count"],
            reading_time_minutes=row["reading_time_minutes"],
            thumbnail_url=f"/api/v1/thumbnails/{row['id']}.webp" if row["thumbnail_path"] else None,
            author=row["author"],
            version=row["version"],
            view_count=row["view_count"],
            download_count=row["download_count"],
            popularity_score=row["popularity_score"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            headline=row["headline"],
            rank=float(row["rank"]),
        ))

    # Record search in history
    search_record = SearchHistory(
        query=query_str,
        result_count=total,
        session_id=session_id,
    )
    db.add(search_record)

    # Generate suggestions from similar titles
    suggestions = await _get_suggestions(db, query_str, limit=3)

    return SearchResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        query=query_str,
        suggestions=suggestions,
    )


async def get_search_suggestions(
    db: AsyncSession, partial_query: str, limit: int = 5
) -> list[SearchSuggestion]:
    """Get auto-complete suggestions from titles, tags, and categories."""
    suggestions = []

    # Title suggestions
    title_query = select(Presentation.title).where(
        Presentation.is_active == True,  # noqa: E712
        Presentation.title.ilike(f"%{partial_query}%"),
    ).limit(limit)
    result = await db.execute(title_query)
    for row in result.scalars().all():
        suggestions.append(SearchSuggestion(text=row, type="title"))

    # Recent search suggestions
    recent_query = (
        select(SearchHistory.query)
        .where(SearchHistory.query.ilike(f"%{partial_query}%"))
        .group_by(SearchHistory.query)
        .order_by(desc(func.count()))
        .limit(3)
    )
    result = await db.execute(recent_query)
    for row in result.scalars().all():
        if not any(s.text == row for s in suggestions):
            suggestions.append(SearchSuggestion(text=row, type="recent"))

    return suggestions[:limit]


async def get_search_history(
    db: AsyncSession, session_id: Optional[str] = None, limit: int = 10
) -> list[SearchHistoryItem]:
    """Get recent searches."""
    query = select(SearchHistory).order_by(desc(SearchHistory.searched_at)).limit(limit)
    if session_id:
        query = query.where(SearchHistory.session_id == session_id)
    result = await db.execute(query)
    return [SearchHistoryItem.model_validate(s) for s in result.scalars().all()]


async def _get_suggestions(db: AsyncSession, query_str: str, limit: int = 3) -> list[str]:
    """Get alternative search suggestions based on similar titles."""
    suggestion_query = text("""
        SELECT DISTINCT title
        FROM presentations
        WHERE is_active = true
          AND similarity(title, :q) > 0.15
          AND title != :q
        ORDER BY similarity(title, :q) DESC
        LIMIT :limit
    """)
    result = await db.execute(suggestion_query, {"q": query_str, "limit": limit})
    return [row[0] for row in result.fetchall()]
