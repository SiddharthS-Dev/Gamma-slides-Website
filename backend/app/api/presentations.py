"""Presentation API routes."""

from uuid import UUID
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_settings
from app.services import presentation_service
from app.schemas.presentation import (
    PresentationPage, PresentationDetail, PresentationUpdate,
    ViewEvent, BookmarkCreate, BookmarkResponse,
)

router = APIRouter(prefix="/presentations", tags=["Presentations"])
settings = get_settings()

import logging
logger = logging.getLogger(__name__)



@router.get("", response_model=PresentationPage)
async def list_presentations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    sort_by: str = Query(default="updated_at"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$"),
    category_id: Optional[UUID] = None,
    department_id: Optional[UUID] = None,
    file_type: Optional[str] = None,
    author: Optional[str] = None,
    tag: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    unclassified: Optional[bool] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """List presentations with pagination, sorting, and filtering."""
    print(f"=== DEBUG API ROUTE unclassified={unclassified} (type: {type(unclassified)}) ===")
    return await presentation_service.list_presentations(
        db=db,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        category_id=category_id,
        department_id=department_id,
        file_type=file_type,
        author=author,
        tag=tag,
        date_from=date_from,
        date_to=date_to,
        unclassified=unclassified,
    )


@router.get("/{presentation_id}", response_model=PresentationDetail)
async def get_presentation(
    presentation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single presentation by ID."""
    result = await presentation_service.get_presentation(db, presentation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Presentation not found")
    return result


@router.patch("/{presentation_id}", response_model=PresentationDetail)
async def update_presentation(
    presentation_id: UUID,
    update: PresentationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update presentation metadata."""
    result = await presentation_service.update_presentation(db, presentation_id, update)
    if not result:
        raise HTTPException(status_code=404, detail="Presentation not found")
    return result


@router.get("/{presentation_id}/file")
async def get_presentation_file(
    presentation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Stream presentation file for viewing. Automatically converts PPTX to PDF for browser rendering."""
    from app.models.presentation import Presentation
    from sqlalchemy import select
    
    result = await db.execute(select(Presentation).where(Presentation.id == presentation_id))
    pres = result.scalar_one_or_none()
    if not pres or not pres.is_active:
        raise HTTPException(status_code=404, detail="Presentation not found")

    file_path = Path(pres.file_path)

    # Security: validate path is within allowed directory
    try:
        file_path.resolve().relative_to(settings.presentations_path.resolve())
    except (ValueError, FileNotFoundError):
        pass

    # Cache-aside download if file does not exist on disk
    if not file_path.exists():
        if not pres.dropbox_id:
            raise HTTPException(status_code=404, detail="File not found locally and not linked to Dropbox")
        
        logger.info(f"Cache miss for presentation {pres.id}. Downloading from Dropbox path: {pres.dropbox_path}")
        from app.services.dropbox_sync_service import get_dropbox_client
        client = get_dropbox_client()
        if not client:
            raise HTTPException(status_code=503, detail="Dropbox credentials not configured on backend")
            
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            import asyncio
            await asyncio.to_thread(
                client.files_download_to_file,
                str(file_path),
                pres.dropbox_id
            )
            logger.info(f"Successfully downloaded {pres.file_name} from Dropbox.")
            
            # Preconvert if it's PPTX
            if pres.file_type == "pptx":
                from app.services.pdf_converter import preconvert_presentation_by_id
                await preconvert_presentation_by_id(str(pres.id), str(file_path))
        except Exception as e:
            logger.error(f"Failed to download file {pres.id} on demand: {e}")
            raise HTTPException(status_code=502, detail=f"Failed to fetch file from Dropbox: {e}")

    # If it is a PPTX file and we have a cached PDF copy, serve the PDF instead
    # to enable fast, inline browser rendering without downloading the PPTX.
    if pres.file_type == "pptx":
        cache_pdf_path = settings.cache_path / f"{presentation_id}.pdf"
        if not cache_pdf_path.exists():
            from app.services.pdf_converter import preconvert_presentation_by_id
            await preconvert_presentation_by_id(str(pres.id), str(file_path))
        if cache_pdf_path.exists():
            file_path = cache_pdf_path

    # Content types
    content_types = {
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "pdf": "application/pdf",
        "html": "text/html",
    }
    
    file_ext = file_path.suffix.lower().lstrip('.')
    content_type = content_types.get(file_ext, "application/octet-stream")
    served_filename = file_path.name if file_ext == "pdf" else pres.file_name

    return FileResponse(
        path=str(file_path),
        media_type=content_type,
        filename=served_filename,
        content_disposition_type="inline",
    )


@router.get("/{presentation_id}/download")
async def download_presentation(
    presentation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Download presentation file for offline use."""
    from app.models.presentation import Presentation
    from sqlalchemy import select
    
    result = await db.execute(select(Presentation).where(Presentation.id == presentation_id))
    pres = result.scalar_one_or_none()
    if not pres or not pres.is_active:
        raise HTTPException(status_code=404, detail="Presentation not found")

    file_path = Path(pres.file_path)

    # Security check
    try:
        file_path.resolve().relative_to(settings.presentations_path.resolve())
    except (ValueError, FileNotFoundError):
        pass

    # Cache-aside download if file does not exist on disk
    if not file_path.exists():
        if not pres.dropbox_id:
            raise HTTPException(status_code=404, detail="File not found locally and not linked to Dropbox")
        
        logger.info(f"Cache miss for presentation {pres.id} during download. Downloading from Dropbox...")
        from app.services.dropbox_sync_service import get_dropbox_client
        client = get_dropbox_client()
        if not client:
            raise HTTPException(status_code=503, detail="Dropbox credentials not configured on backend")
            
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            import asyncio
            await asyncio.to_thread(
                client.files_download_to_file,
                str(file_path),
                pres.dropbox_id
            )
            logger.info(f"Successfully downloaded {pres.file_name} from Dropbox.")
        except Exception as e:
            logger.error(f"Failed to download file {pres.id} on demand: {e}")
            raise HTTPException(status_code=502, detail=f"Failed to fetch file from Dropbox: {e}")

    # Record download
    await presentation_service.record_download(db, presentation_id)

    return FileResponse(
        path=str(file_path),
        filename=pres.file_name,
        media_type="application/octet-stream",
    )


@router.post("/{presentation_id}/view")
async def record_view(
    presentation_id: UUID,
    event: ViewEvent,
    db: AsyncSession = Depends(get_db),
):
    """Record a presentation view event."""
    success = await presentation_service.record_view(db, presentation_id, event)
    if not success:
        raise HTTPException(status_code=404, detail="Presentation not found")
    return {"status": "recorded"}


@router.post("/{presentation_id}/bookmarks", response_model=BookmarkResponse)
async def create_bookmark(
    presentation_id: UUID,
    bookmark: BookmarkCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a bookmark on a presentation slide."""
    result = await presentation_service.create_bookmark(db, presentation_id, bookmark)
    if not result:
        raise HTTPException(status_code=404, detail="Presentation not found")
    return result


@router.get("/{presentation_id}/bookmarks", response_model=list[BookmarkResponse])
async def get_bookmarks(
    presentation_id: UUID,
    session_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get bookmarks for a presentation."""
    return await presentation_service.get_bookmarks(db, presentation_id, session_id)


@router.delete("/bookmarks/{bookmark_id}")
async def delete_bookmark(
    bookmark_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a bookmark."""
    success = await presentation_service.delete_bookmark(db, bookmark_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return {"status": "deleted"}
