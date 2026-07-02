"""Presentation service — business logic for CRUD, filtering, and pagination."""

import math
from uuid import UUID
from typing import Optional
from datetime import datetime

from sqlalchemy import select, func, desc, asc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.presentation import Presentation, PresentationTag
from app.models.category import Category
from app.models.department import Department
from app.models.tag import Tag
from app.models.analytics import ViewHistory, Bookmark
from app.schemas.presentation import (
    PresentationListItem, PresentationDetail, PresentationPage,
    PresentationUpdate, ViewEvent, BookmarkCreate, BookmarkResponse,
    CategoryBrief, DepartmentBrief, TagBrief,
)
from app.config import get_settings

settings = get_settings()


def _build_thumbnail_url(presentation: Presentation) -> Optional[str]:
    """Build thumbnail URL from presentation."""
    if presentation.thumbnail_path:
        return f"/api/v1/thumbnails/{presentation.id}.webp"
    return None


def _to_list_item(p: Presentation) -> PresentationListItem:
    """Convert ORM model to list item schema."""
    is_cached = p.file_type in ("pdf", "html") or (settings.cache_path / f"{p.id}.pdf").exists()
    return PresentationListItem(
        id=p.id,
        title=p.title,
        description=p.description,
        file_name=p.file_name,
        file_type=p.file_type,
        file_size=p.file_size,
        slide_count=p.slide_count,
        reading_time_minutes=p.reading_time_minutes,
        thumbnail_url=_build_thumbnail_url(p),
        category=CategoryBrief.model_validate(p.category) if p.category else None,
        department=DepartmentBrief.model_validate(p.department) if p.department else None,
        tags=[TagBrief.model_validate(t) for t in p.tags] if p.tags else [],
        author=p.author,
        version=p.version,
        view_count=p.view_count,
        download_count=p.download_count,
        popularity_score=p.popularity_score,
        created_at=p.created_at,
        updated_at=p.updated_at,
        is_offline_available=is_cached,
    )


# Sort mapping
SORT_COLUMNS = {
    "title": Presentation.title,
    "created_at": Presentation.created_at,
    "updated_at": Presentation.updated_at,
    "popularity_score": Presentation.popularity_score,
    "view_count": Presentation.view_count,
    "file_size": Presentation.file_size,
}


async def list_presentations(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 24,
    sort_by: str = "updated_at",
    sort_order: str = "desc",
    category_id: Optional[UUID] = None,
    department_id: Optional[UUID] = None,
    file_type: Optional[str] = None,
    author: Optional[str] = None,
    tag: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    unclassified: Optional[bool] = None,
) -> PresentationPage:
    """List presentations with pagination, sorting, and filtering."""
    # Base query
    query = select(Presentation).where(Presentation.is_active == True)  # noqa: E712

    # Apply filters
    if category_id:
        query = query.where(Presentation.category_id == category_id)
    if department_id:
        query = query.where(Presentation.department_id == department_id)
    if file_type:
        query = query.where(Presentation.file_type == file_type.lower())
    if author:
        query = query.where(Presentation.author.ilike(f"%{author}%"))
    if date_from:
        query = query.where(Presentation.created_at >= date_from)
    if date_to:
        query = query.where(Presentation.created_at <= date_to)
    if tag:
        query = query.join(PresentationTag).join(Tag).where(Tag.slug == tag)
    if unclassified is True:
        query = query.where(Presentation.category_id.is_(None))
    elif unclassified is False:
        query = query.where(Presentation.category_id.is_not(None))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Apply sorting
    sort_col = SORT_COLUMNS.get(sort_by, Presentation.updated_at)
    if sort_order == "asc":
        query = query.order_by(asc(sort_col))
    else:
        query = query.order_by(desc(sort_col))

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute
    result = await db.execute(query)
    presentations = result.scalars().unique().all()

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PresentationPage(
        items=[_to_list_item(p) for p in presentations],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


async def get_presentation(db: AsyncSession, presentation_id: UUID) -> Optional[PresentationDetail]:
    """Get a single presentation by ID."""
    query = select(Presentation).where(
        Presentation.id == presentation_id,
        Presentation.is_active == True,  # noqa: E712
    )
    result = await db.execute(query)
    p = result.scalar_one_or_none()
    if not p:
        return None

    is_cached = p.file_type in ("pdf", "html") or (settings.cache_path / f"{p.id}.pdf").exists()
    return PresentationDetail(
        id=p.id,
        title=p.title,
        description=p.description,
        file_name=p.file_name,
        file_path=p.file_path,
        file_type=p.file_type,
        file_size=p.file_size,
        file_hash=p.file_hash,
        slide_count=p.slide_count,
        reading_time_minutes=p.reading_time_minutes,
        thumbnail_url=_build_thumbnail_url(p),
        category=CategoryBrief.model_validate(p.category) if p.category else None,
        department=DepartmentBrief.model_validate(p.department) if p.department else None,
        tags=[TagBrief.model_validate(t) for t in p.tags] if p.tags else [],
        author=p.author,
        version=p.version,
        view_count=p.view_count,
        download_count=p.download_count,
        popularity_score=p.popularity_score,
        created_at=p.created_at,
        updated_at=p.updated_at,
        file_modified_at=p.file_modified_at,
        last_viewed_at=p.last_viewed_at,
        is_active=p.is_active,
        is_offline_available=is_cached,
    )


async def update_presentation(
    db: AsyncSession, presentation_id: UUID, update: PresentationUpdate
) -> Optional[PresentationDetail]:
    """Update presentation metadata."""
    query = select(Presentation).where(Presentation.id == presentation_id)
    result = await db.execute(query)
    p = result.scalar_one_or_none()
    if not p:
        return None

    update_data = update.model_dump(exclude_unset=True)
    tag_ids = update_data.pop("tag_ids", None)

    for key, value in update_data.items():
        setattr(p, key, value)

    if tag_ids is not None:
        tag_query = select(Tag).where(Tag.id.in_(tag_ids))
        tags_result = await db.execute(tag_query)
        p.tags = list(tags_result.scalars().all())

    p.updated_at = datetime.utcnow()
    await db.flush()

    return await get_presentation(db, presentation_id)


async def record_view(
    db: AsyncSession, presentation_id: UUID, event: ViewEvent
) -> bool:
    """Record a presentation view event."""
    query = select(Presentation).where(Presentation.id == presentation_id)
    result = await db.execute(query)
    p = result.scalar_one_or_none()
    if not p:
        return False

    # Update counters
    p.view_count += 1
    p.last_viewed_at = datetime.utcnow()

    # Recalculate popularity (simple weighted score)
    p.popularity_score = (p.view_count * 1.0) + (p.download_count * 2.0)

    # Create view history record
    view = ViewHistory(
        presentation_id=presentation_id,
        session_id=event.session_id,
        last_slide=event.slide_number,
        duration_seconds=event.duration_seconds,
    )
    db.add(view)
    await db.flush()
    return True


async def record_download(db: AsyncSession, presentation_id: UUID) -> bool:
    """Increment download counter."""
    query = select(Presentation).where(Presentation.id == presentation_id)
    result = await db.execute(query)
    p = result.scalar_one_or_none()
    if not p:
        return False

    p.download_count += 1
    p.popularity_score = (p.view_count * 1.0) + (p.download_count * 2.0)
    await db.flush()
    return True


async def create_bookmark(
    db: AsyncSession, presentation_id: UUID, bookmark: BookmarkCreate
) -> Optional[BookmarkResponse]:
    """Create a bookmark on a presentation slide."""
    b = Bookmark(
        presentation_id=presentation_id,
        slide_number=bookmark.slide_number,
        note=bookmark.note,
        session_id=bookmark.session_id,
    )
    db.add(b)
    await db.flush()
    return BookmarkResponse.model_validate(b)


async def get_bookmarks(
    db: AsyncSession, presentation_id: UUID, session_id: Optional[str] = None
) -> list[BookmarkResponse]:
    """Get bookmarks for a presentation."""
    query = select(Bookmark).where(Bookmark.presentation_id == presentation_id)
    if session_id:
        query = query.where(Bookmark.session_id == session_id)
    query = query.order_by(Bookmark.slide_number)
    result = await db.execute(query)
    return [BookmarkResponse.model_validate(b) for b in result.scalars().all()]


async def delete_bookmark(db: AsyncSession, bookmark_id: UUID) -> bool:
    """Delete a bookmark."""
    query = select(Bookmark).where(Bookmark.id == bookmark_id)
    result = await db.execute(query)
    b = result.scalar_one_or_none()
    if not b:
        return False
    await db.delete(b)
    await db.flush()
    return True
