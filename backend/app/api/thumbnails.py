"""Thumbnail serving route."""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import get_settings

router = APIRouter(prefix="/thumbnails", tags=["Thumbnails"])
settings = get_settings()


@router.get("/{filename}")
async def get_thumbnail(filename: str):
    """Serve thumbnail image files."""
    # Security: strip path components, allow only expected filenames
    safe_name = Path(filename).name
    if not safe_name or ".." in safe_name:
        raise HTTPException(status_code=400, detail="Invalid filename")

    thumb_path = settings.thumbnails_path / safe_name

    # Try WebP, then JPG, then PNG
    for ext in ["", ".webp", ".jpg", ".png"]:
        candidate = thumb_path if ext == "" else thumb_path.with_suffix(ext)
        if candidate.exists() and candidate.is_file():
            media_types = {
                ".webp": "image/webp",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
            }
            media_type = media_types.get(candidate.suffix.lower(), "image/webp")
            return FileResponse(
                path=str(candidate),
                media_type=media_type,
                headers={"Cache-Control": "public, max-age=86400"},
            )

    raise HTTPException(status_code=404, detail="Thumbnail not found")
