"""Auto-ingestion engine — scans directories, extracts metadata, generates thumbnails.

After successful ingestion, triggers AI classification in the background.
"""

import asyncio
import hashlib
import logging
import re
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.presentation import Presentation
from app.models.ingestion import IngestionLog
from app.config import get_settings
from app.ingestion.metadata_extractor import extract_metadata
from app.ingestion.thumbnail_generator import generate_thumbnail
from app.services.category_service import get_or_create_tag

logger = logging.getLogger(__name__)
settings = get_settings()


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def title_from_filename(filename: str) -> str:
    """Generate a human-readable title from a filename.

    Examples:
        'Inspironics-Exit-Bridge-Participation-Impact.pptx' → 'Inspironics Exit Bridge Participation Impact'
        'CK-PLM-Building-the-Operational-Intelligence-Layer.pptx' → 'CK PLM Building The Operational Intelligence Layer'
    """
    # Remove extension
    name = Path(filename).stem
    # Remove trailing version indicators like (1), (2)
    name = re.sub(r'\s*\(\d+\)\s*$', '', name)
    # Replace hyphens and underscores with spaces
    name = name.replace('-', ' ').replace('_', ' ')
    # Clean up multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()
    # Title case
    return name.title() if name == name.lower() else name


def extract_auto_tags(filename: str) -> list[str]:
    """Extract potential tags from filename keywords."""
    name = Path(filename).stem.lower()
    # Split on separators
    words = re.split(r'[-_\s]+', name)
    # Filter out common noise words and short words
    noise_words = {'the', 'and', 'for', 'from', 'with', 'into', 'a', 'an', 'of', 'to', 'in', 'on', 'at', 'by', 'or', 'vs', 'v1', 'v2'}
    tags = [w for w in words if len(w) > 2 and w not in noise_words and not w.isdigit()]
    # Remove duplicates preserving order and limit
    seen = set()
    unique_tags = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)
    return unique_tags[:8]


async def ingest_file(file_path: Path) -> Optional[str]:
    """Ingest a single presentation file.

    Returns the presentation ID if successful, None if skipped/failed.
    """
    async with async_session_factory() as db:
        log_entry = IngestionLog(file_path=str(file_path), status="processing")
        db.add(log_entry)
        await db.flush()

        try:
            # Check file extension
            ext = file_path.suffix.lower()
            if ext not in settings.supported_extensions_list:
                log_entry.status = "skipped"
                log_entry.error_message = f"Unsupported extension: {ext}"
                log_entry.completed_at = datetime.utcnow()
                await db.commit()
                return None

            # Compute hash
            file_hash = compute_file_hash(file_path)
            log_entry.file_hash = file_hash

            # Check if already indexed
            existing = await db.execute(
                select(Presentation).where(Presentation.file_hash == file_hash)
            )
            if existing.scalar_one_or_none():
                log_entry.status = "skipped"
                log_entry.error_message = "Already indexed (same hash)"
                log_entry.completed_at = datetime.utcnow()
                await db.commit()
                logger.info(f"Skipped (already indexed): {file_path.name}")
                return None

            # Check if same path exists (file was updated)
            existing_by_path = await db.execute(
                select(Presentation).where(Presentation.file_path == str(file_path))
            )
            existing_pres = existing_by_path.scalar_one_or_none()

            # Extract metadata
            metadata = extract_metadata(file_path)

            # Generate title from filename if not found in metadata
            title = metadata.get("title") or title_from_filename(file_path.name)

            # Generate thumbnail
            thumbnail_path = generate_thumbnail(file_path, settings.thumbnails_path)

            # File stats
            stat = file_path.stat()
            file_size = stat.st_size
            file_modified = datetime.fromtimestamp(stat.st_mtime)

            # Estimate reading time (2 minutes per slide, 1 minute per page)
            slide_count = metadata.get("slide_count")
            reading_time = None
            if slide_count:
                reading_time = max(1, slide_count * 2)

            if existing_pres:
                # Update existing record
                existing_pres.title = title
                existing_pres.description = metadata.get("description")
                existing_pres.file_hash = file_hash
                existing_pres.file_size = file_size
                existing_pres.slide_count = slide_count
                existing_pres.reading_time_minutes = reading_time
                existing_pres.thumbnail_path = str(thumbnail_path) if thumbnail_path else None
                existing_pres.author = metadata.get("author")
                existing_pres.file_modified_at = file_modified
                existing_pres.updated_at = datetime.utcnow()
                existing_pres.is_active = True

                pres_id = str(existing_pres.id)
                logger.info(f"Updated: {file_path.name}")
            else:
                # Create new presentation
                pres = Presentation(
                    title=title,
                    description=metadata.get("description"),
                    file_name=file_path.name,
                    file_path=str(file_path),
                    file_type=ext.lstrip('.'),
                    file_size=file_size,
                    file_hash=file_hash,
                    slide_count=slide_count,
                    reading_time_minutes=reading_time,
                    thumbnail_path=str(thumbnail_path) if thumbnail_path else None,
                    author=metadata.get("author"),
                    version="1.0",
                    file_modified_at=file_modified,
                )

                # Auto-tag
                auto_tags = extract_auto_tags(file_path.name)
                for tag_name in auto_tags:
                    tag = await get_or_create_tag(db, tag_name)
                    pres.tags.append(tag)

                db.add(pres)
                await db.flush()
                pres_id = str(pres.id)
                logger.info(f"Ingested: {file_path.name}")

            log_entry.status = "success"
            log_entry.completed_at = datetime.utcnow()
            await db.commit()

            # Trigger AI classification in the background
            if settings.classification_auto_enabled:
                asyncio.create_task(
                    _classify_in_background(UUID(pres_id))
                )

            return pres_id

        except Exception as e:
            log_entry.status = "failed"
            log_entry.error_message = str(e)
            log_entry.completed_at = datetime.utcnow()
            await db.commit()
            logger.error(f"Failed to ingest {file_path.name}: {e}")
            return None


async def scan_directory(directory: Path) -> dict:
    """Scan a directory for new/updated presentations.

    Returns a summary dict with counts.
    """
    logger.info(f"Scanning directory: {directory}")
    results = {"scanned": 0, "ingested": 0, "skipped": 0, "failed": 0}

    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        return results

    for file_path in directory.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in settings.supported_extensions_list:
            results["scanned"] += 1
            result = await ingest_file(file_path)
            if result:
                results["ingested"] += 1
            else:
                results["skipped"] += 1

    logger.info(f"Scan complete: {results}")
    return results


async def full_reindex(directory: Path) -> dict:
    """Force reindex all presentations (deactivate missing, re-scan all)."""
    async with async_session_factory() as db:
        # Mark all presentations from this directory as inactive
        result = await db.execute(
            select(Presentation).where(
                Presentation.file_path.like(f"{directory}%")
            )
        )
        for pres in result.scalars().all():
            if not Path(pres.file_path).exists():
                pres.is_active = False
                logger.info(f"Deactivated (file missing): {pres.file_name}")
        await db.commit()

    # Re-scan
    return await scan_directory(directory)


# Sequential background classification task queue
_classification_queue = asyncio.Queue()
_classification_worker_task = None


async def _classification_worker():
    while True:
        presentation_id = await _classification_queue.get()
        try:
            from app.database import async_session_factory
            from app.services.classification_service import classify_presentation
            from app.services.similarity_service import compute_similarity_for_presentation

            async with async_session_factory() as db:
                result = await classify_presentation(db, presentation_id)
                if result.get("status") in ("classified", "pending_review"):
                    # Also compute similarities against existing presentations
                    await compute_similarity_for_presentation(db, presentation_id)
                await db.commit()
                logger.info(f"Background classification complete: {result.get('status')} for {presentation_id}")
        except Exception as e:
            logger.error(f"Background classification failed for {presentation_id}: {e}")
        finally:
            _classification_queue.task_done()


def _start_classification_worker():
    global _classification_worker_task
    if _classification_worker_task is None or _classification_worker_task.done():
        _classification_worker_task = asyncio.create_task(_classification_worker())


async def _classify_in_background(presentation_id: UUID) -> None:
    """Run AI classification sequentially in the background via queue so ingestion isn't blocked."""
    _start_classification_worker()
    await _classification_queue.put(presentation_id)
