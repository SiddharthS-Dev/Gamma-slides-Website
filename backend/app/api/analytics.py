"""Analytics and Admin API routes."""

from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_settings
from app.services import analytics_service
from app.schemas.analytics import AnalyticsSummary, SearchStats, StorageStats, IngestionStatus
from app.services.dropbox_sync_service import dropbox_sync_service

settings = get_settings()

analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])


# Analytics endpoints
@analytics_router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(db: AsyncSession = Depends(get_db)):
    """Get dashboard analytics summary with trending, most viewed, recently added."""
    return await analytics_service.get_analytics_summary(db)


@analytics_router.get("/trending")
async def get_trending(
    days: int = 7,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """Get trending presentations."""
    return await analytics_service.get_trending(db, days, limit)


@analytics_router.get("/most-viewed")
async def get_most_viewed(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Get most viewed presentations all time."""
    return await analytics_service.get_most_viewed(db, limit)


@analytics_router.get("/recently-added")
async def get_recently_added(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Get recently added presentations."""
    return await analytics_service.get_recently_added(db, limit)


@analytics_router.get("/search-stats", response_model=SearchStats)
async def get_search_stats(db: AsyncSession = Depends(get_db)):
    """Get search analytics."""
    return await analytics_service.get_search_stats(db)


# Admin endpoints
@admin_router.post("/reindex")
async def reindex_presentations():
    """Force full reindex of all presentations from Dropbox."""
    await dropbox_sync_service._clear_cursor()
    result = await dropbox_sync_service.sync()
    return {"status": "completed", "result": result}


@admin_router.post("/scan")
async def trigger_scan():
    """Trigger an immediate scan/sync for new presentations from Dropbox."""
    result = await dropbox_sync_service.sync()
    return {"status": "completed", "result": result}


@admin_router.post("/regenerate-thumbnails")
async def regenerate_thumbnails(db: AsyncSession = Depends(get_db)):
    """Regenerate all thumbnails."""
    from app.models.presentation import Presentation
    from app.ingestion.thumbnail_generator import generate_thumbnail
    from sqlalchemy import select

    result = await db.execute(select(Presentation).where(Presentation.is_active == True))  # noqa: E712
    count = 0
    for pres in result.scalars().all():
        file_path = Path(pres.file_path)
        if file_path.exists():
            # Delete existing thumbnail
            if pres.thumbnail_path:
                thumb = Path(pres.thumbnail_path)
                thumb.unlink(missing_ok=True)

            # Regenerate
            new_thumb = generate_thumbnail(file_path, settings.thumbnails_path)
            pres.thumbnail_path = str(new_thumb) if new_thumb else None
            count += 1

    return {"status": "completed", "thumbnails_regenerated": count}


@admin_router.get("/storage-stats", response_model=StorageStats)
async def get_storage_stats(db: AsyncSession = Depends(get_db)):
    """Get storage monitoring stats."""
    return await analytics_service.get_storage_stats(db)


@admin_router.get("/ingestion-status", response_model=IngestionStatus)
async def get_ingestion_status():
    """Get ingestion engine status."""
    status = dropbox_sync_service.get_status()
    from datetime import datetime
    return IngestionStatus(
        is_running=status["is_running"],
        last_scan_at=datetime.fromtimestamp(status["last_scan_at"]) if status["last_scan_at"] else None,
        files_processed=status["files_processed"],
        files_failed=status["files_failed"],
        files_skipped=0,
        watch_paths=status["watch_paths"],
    )
