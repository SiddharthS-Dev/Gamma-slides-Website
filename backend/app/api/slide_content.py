"""Slide content API — serves extracted per-slide content for the browser viewer."""

import logging
from uuid import UUID
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.config import get_settings
from app.services import presentation_service
from app.ingestion.content_extractor import extract_full_content

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/presentations", tags=["Slide Content"])
settings = get_settings()


class SlideContent(BaseModel):
    """Single slide content."""
    slide_number: int
    heading: str = ""
    body: str = ""
    speaker_notes: str = ""
    has_image: bool = False


class SlideContentResponse(BaseModel):
    """Full slide content response for a presentation."""
    presentation_id: str
    title: str
    total_slides: int
    slides: list[SlideContent]


@router.get("/{presentation_id}/slides", response_model=SlideContentResponse)
async def get_slide_content(
    presentation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Extract and return per-slide content for the browser viewer.

    Uses the content extraction pipeline to parse the presentation file
    and return structured text content for each slide.
    """
    pres = await presentation_service.get_presentation(db, presentation_id)
    if not pres:
        raise HTTPException(status_code=404, detail="Presentation not found")

    file_path = Path(pres.file_path)

    # Security: validate path is within allowed directory
    try:
        file_path.resolve().relative_to(settings.presentations_path.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    # Extract content using the existing engine
    try:
        content = extract_full_content(file_path)
    except Exception as e:
        logger.error(f"Slide content extraction failed for {pres.file_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to extract slide content")

    # Build per-slide response
    slides: list[SlideContent] = []
    slide_texts = content.slide_texts or []
    headings = content.headings or []
    total = len(slide_texts) if slide_texts else (content.metadata.get("slide_count") or pres.slide_count or 1)

    # Parse speaker notes per slide (they may be concatenated)
    notes_parts = content.speaker_notes.split("\n\n") if content.speaker_notes else []

    for i in range(max(total, len(slide_texts))):
        slide_text = slide_texts[i] if i < len(slide_texts) else ""

        # Try to find a heading for this slide
        # Heuristic: check if slide text starts with any known heading
        slide_heading = ""
        slide_body = slide_text

        for h in headings:
            if h and slide_text.startswith(h):
                slide_heading = h
                slide_body = slide_text[len(h):].strip()
                break

        # If no match, try splitting on first sentence boundary for short first lines
        if not slide_heading and slide_text:
            lines = slide_text.split("\n")
            if lines and len(lines[0]) < 150:
                slide_heading = lines[0].strip()
                slide_body = "\n".join(lines[1:]).strip()

        # Speaker notes for this slide
        slide_notes = notes_parts[i] if i < len(notes_parts) else ""

        slides.append(SlideContent(
            slide_number=i + 1,
            heading=slide_heading,
            body=slide_body,
            speaker_notes=slide_notes,
            has_image=False,  # We don't extract images yet
        ))

    return SlideContentResponse(
        presentation_id=str(presentation_id),
        title=content.title or pres.title,
        total_slides=len(slides),
        slides=slides,
    )
