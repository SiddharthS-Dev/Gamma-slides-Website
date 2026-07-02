"""Analytics service — trending, most viewed, search stats."""

from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy import select, func, desc, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.presentation import Presentation
from app.models.analytics import ViewHistory, SearchHistory
from app.models.category import Category
from app.models.tag import Tag
from app.schemas.analytics import (
    TrendingItem, AnalyticsSummary, SearchStats, StorageStats,
)
from app.config import get_settings

settings = get_settings()


async def get_analytics_summary(db: AsyncSession) -> AnalyticsSummary:
    """Get dashboard analytics summary."""
    # Total presentations
    total_pres = (await db.execute(
        select(func.count()).where(Presentation.is_active == True)  # noqa: E712
    )).scalar() or 0

    # Total views
    total_views = (await db.execute(
        select(func.sum(Presentation.view_count))
    )).scalar() or 0

    # Total downloads
    total_downloads = (await db.execute(
        select(func.sum(Presentation.download_count))
    )).scalar() or 0

    # Total categories
    total_cats = (await db.execute(select(func.count(Category.id)))).scalar() or 0

    # Total tags
    total_tags = (await db.execute(select(func.count(Tag.id)))).scalar() or 0

    # Total storage
    total_storage = (await db.execute(
        select(func.sum(Presentation.file_size)).where(Presentation.is_active == True)  # noqa: E712
    )).scalar() or 0

    # Trending (most views in last 7 days)
    trending = await get_trending(db, days=7, limit=6)

    # Most viewed all time
    most_viewed = await get_most_viewed(db, limit=6)

    # Recently added
    recently_added = await get_recently_added(db, limit=6)

    return AnalyticsSummary(
        total_presentations=total_pres,
        total_views=total_views,
        total_downloads=total_downloads,
        total_categories=total_cats,
        total_tags=total_tags,
        total_storage_bytes=total_storage,
        trending=trending,
        most_viewed=most_viewed,
        recently_added=recently_added,
    )


async def get_trending(db: AsyncSession, days: int = 7, limit: int = 10) -> list[TrendingItem]:
    """Get trending presentations based on recent views."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    query = (
        select(
            Presentation.id,
            Presentation.title,
            Presentation.thumbnail_path,
            Presentation.view_count,
            Presentation.file_type,
            Presentation.created_at,
            func.count(ViewHistory.id).label("recent_views"),
        )
        .outerjoin(ViewHistory, (ViewHistory.presentation_id == Presentation.id) & (ViewHistory.viewed_at >= cutoff))
        .where(Presentation.is_active == True)  # noqa: E712
        .group_by(Presentation.id, Presentation.title, Presentation.thumbnail_path, Presentation.view_count, Presentation.file_type, Presentation.created_at)
        .order_by(desc("recent_views"))
        .limit(limit)
    )
    result = await db.execute(query)

    items = []
    for row in result.all():
        items.append(TrendingItem(
            id=row.id,
            title=row.title,
            thumbnail_url=f"/api/v1/thumbnails/{row.id}.webp" if row.thumbnail_path else None,
            view_count=row.view_count,
            trend_score=float(row.recent_views or 0),
            file_type=row.file_type,
            created_at=row.created_at,
        ))
    return items


async def get_most_viewed(db: AsyncSession, limit: int = 10) -> list[TrendingItem]:
    """Get most viewed presentations all time."""
    query = (
        select(Presentation)
        .where(Presentation.is_active == True)  # noqa: E712
        .order_by(desc(Presentation.view_count))
        .limit(limit)
    )
    result = await db.execute(query)
    return [
        TrendingItem(
            id=p.id,
            title=p.title,
            thumbnail_url=f"/api/v1/thumbnails/{p.id}.webp" if p.thumbnail_path else None,
            view_count=p.view_count,
            trend_score=p.popularity_score,
            file_type=p.file_type,
            created_at=p.created_at,
        )
        for p in result.scalars().all()
    ]


async def get_recently_added(db: AsyncSession, limit: int = 10) -> list[TrendingItem]:
    """Get recently added presentations."""
    query = (
        select(Presentation)
        .where(Presentation.is_active == True)  # noqa: E712
        .order_by(desc(Presentation.created_at))
        .limit(limit)
    )
    result = await db.execute(query)
    return [
        TrendingItem(
            id=p.id,
            title=p.title,
            thumbnail_url=f"/api/v1/thumbnails/{p.id}.webp" if p.thumbnail_path else None,
            view_count=p.view_count,
            trend_score=p.popularity_score,
            file_type=p.file_type,
            created_at=p.created_at,
        )
        for p in result.scalars().all()
    ]


async def get_search_stats(db: AsyncSession) -> SearchStats:
    """Get search analytics."""
    total = (await db.execute(select(func.count(SearchHistory.id)))).scalar() or 0
    unique = (await db.execute(
        select(func.count(func.distinct(SearchHistory.query)))
    )).scalar() or 0

    # Top queries
    top_query = (
        select(SearchHistory.query, func.count().label("count"))
        .group_by(SearchHistory.query)
        .order_by(desc("count"))
        .limit(10)
    )
    result = await db.execute(top_query)
    top_queries = [{"query": row.query, "count": row.count} for row in result.all()]

    # Zero-result queries
    zero_query = (
        select(SearchHistory.query)
        .where(SearchHistory.result_count == 0)
        .group_by(SearchHistory.query)
        .order_by(desc(func.count()))
        .limit(10)
    )
    result = await db.execute(zero_query)
    zero_results = [row[0] for row in result.all()]

    return SearchStats(
        total_searches=total,
        unique_queries=unique,
        top_queries=top_queries,
        zero_result_queries=zero_results,
    )


async def get_storage_stats(db: AsyncSession) -> StorageStats:
    """Get storage statistics."""
    total_files = (await db.execute(
        select(func.count()).where(Presentation.is_active == True)  # noqa: E712
    )).scalar() or 0

    total_size = (await db.execute(
        select(func.sum(Presentation.file_size)).where(Presentation.is_active == True)  # noqa: E712
    )).scalar() or 0

    # By type
    type_query = (
        select(Presentation.file_type, func.count(), func.sum(Presentation.file_size))
        .where(Presentation.is_active == True)  # noqa: E712
        .group_by(Presentation.file_type)
    )
    result = await db.execute(type_query)
    by_type = {}
    for row in result.all():
        by_type[row[0]] = {"count": row[1], "size": row[2] or 0}

    return StorageStats(
        total_files=total_files,
        total_size_bytes=total_size,
        by_type=by_type,
        thumbnail_count=0,
        thumbnail_size_bytes=0,
    )
