"""Dropbox synchronization service.

Replaces local file watcher with a cursor-based delta syncing system.
"""

import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

import dropbox
from dropbox.files import FileMetadata, FolderMetadata, DeletedMetadata
from sqlalchemy import select

from app.config import get_settings
from app.database import async_session_factory
from app.models.presentation import Presentation
from app.models.sync_state import SyncState
from app.models.ingestion import IngestionLog
from app.ingestion.metadata_extractor import extract_metadata
from app.ingestion.thumbnail_generator import generate_thumbnail
from app.services.category_service import get_or_create_tag
from app.ingestion.content_extractor import extract_full_content
from app.ingestion.scanner import compute_file_hash, title_from_filename, extract_auto_tags

logger = logging.getLogger(__name__)
settings = get_settings()


def get_dropbox_client() -> Optional[dropbox.Dropbox]:
    """Initialize the Dropbox client using refresh token OAuth credentials."""
    if not settings.dropbox_refresh_token or not settings.dropbox_app_key or not settings.dropbox_app_secret:
        logger.warning("Dropbox credentials are not fully configured. Synchronization will be disabled.")
        return None
    try:
        return dropbox.Dropbox(
            oauth2_refresh_token=settings.dropbox_refresh_token,
            app_key=settings.dropbox_app_key,
            app_secret=settings.dropbox_app_secret
        )
    except Exception as e:
        logger.error(f"Failed to initialize Dropbox client: {e}")
        return None


class DropboxSyncService:
    """Manages delta synchronization between Dropbox folder and PostgreSQL database.

    Runs in a background loop or can be triggered manually.
    """

    def __init__(self):
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.last_sync_at: Optional[datetime] = None
        self.sync_status = "idle"  # idle, syncing, failed
        self.files_processed = 0
        self.files_failed = 0
        self.last_error: Optional[str] = None

    async def start(self):
        """Start the sync service background task."""
        if self.is_running:
            logger.warning("Dropbox Sync Service is already running.")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._sync_loop())
        logger.info(f"Dropbox Sync Service started — folder: {settings.dropbox_folder_path}, interval: {settings.dropbox_sync_interval_seconds}s")

    async def stop(self):
        """Stop the sync service background task."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Dropbox Sync Service stopped.")

    async def _sync_loop(self):
        """Main synchronization loop."""
        # Wait a few seconds after startup before the initial sync
        await asyncio.sleep(5)
        while self.is_running:
            try:
                await self.sync()
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
            await asyncio.sleep(settings.dropbox_sync_interval_seconds)

    async def sync(self) -> Dict[str, Any]:
        """Perform a single sync cycle."""
        client = get_dropbox_client()
        if not client:
            return {"status": "skipped", "reason": "Dropbox credentials not configured"}

        self.sync_status = "syncing"
        logger.info("Starting Dropbox sync cycle...")
        results = {"processed": 0, "failed": 0, "deleted": 0, "status": "success"}

        try:
            # 1. Fetch cursor from DB
            cursor = await self._get_saved_cursor()
            
            # 2. Query changes
            entries = []
            new_cursor = None
            has_more = True
            
            if not cursor:
                # Initial sync - recursively list all files
                logger.info(f"Initial sync: Listing all folder contents recursively from root {settings.dropbox_folder_path}...")
                res = await asyncio.to_thread(
                    client.files_list_folder,
                    path=settings.dropbox_folder_path,
                    recursive=True
                )
                entries.extend(res.entries)
                new_cursor = res.cursor
                has_more = res.has_more
                
                while has_more:
                    res = await asyncio.to_thread(
                        client.files_list_folder_continue,
                        cursor=new_cursor
                    )
                    entries.extend(res.entries)
                    new_cursor = res.cursor
                    has_more = res.has_more
            else:
                # Delta sync - retrieve changes since cursor
                logger.info("Delta sync: Listing folder changes from last cursor...")
                try:
                    res = await asyncio.to_thread(
                        client.files_list_folder_continue,
                        cursor=cursor
                    )
                    entries.extend(res.entries)
                    new_cursor = res.cursor
                    has_more = res.has_more
                    
                    while has_more:
                        res = await asyncio.to_thread(
                            client.files_list_folder_continue,
                            cursor=new_cursor
                        )
                        entries.extend(res.entries)
                        new_cursor = res.cursor
                        has_more = res.has_more
                except dropbox.exceptions.ApiError as api_err:
                    # Handle cursor expiration or reset
                    if api_err.error.is_reset() or "reset" in str(api_err).lower():
                        logger.warning("Dropbox sync cursor expired or reset. Performing full re-index...")
                        await self._clear_cursor()
                        return await self.sync()
                    else:
                        raise

            # 3. Process changes
            for entry in entries:
                try:
                    if isinstance(entry, FileMetadata):
                        ext = Path(entry.name).suffix.lower()
                        if ext not in settings.supported_extensions_list:
                            continue
                        
                        success = await self._process_file(client, entry)
                        if success:
                            results["processed"] += 1
                            self.files_processed += 1
                        else:
                            results["failed"] += 1
                            self.files_failed += 1
                            
                    elif isinstance(entry, DeletedMetadata):
                        success = await self._process_deletion(entry)
                        if success:
                            results["deleted"] += 1
                            
                except Exception as entry_e:
                    logger.error(f"Error processing entry {entry.name}: {entry_e}")
                    results["failed"] += 1
                    self.files_failed += 1

            # 4. Save cursor
            if new_cursor:
                await self._save_cursor(new_cursor)
                
            self.last_sync_at = datetime.utcnow()
            self.sync_status = "idle"
            self.last_error = None
            logger.info(f"Dropbox sync cycle completed. Results: {results}")
            return results

        except Exception as e:
            self.sync_status = "failed"
            self.last_error = str(e)
            logger.error(f"Dropbox sync cycle failed: {e}")
            results["status"] = "failed"
            results["error"] = str(e)
            return results

    async def _get_saved_cursor(self) -> Optional[str]:
        async with async_session_factory() as db:
            result = await db.execute(
                select(SyncState).where(SyncState.key == "dropbox_cursor")
            )
            state = result.scalar_one_or_none()
            return state.value if state else None

    async def _save_cursor(self, cursor: str):
        async with async_session_factory() as db:
            result = await db.execute(
                select(SyncState).where(SyncState.key == "dropbox_cursor")
            )
            state = result.scalar_one_or_none()
            if state:
                state.value = cursor
                state.updated_at = datetime.utcnow()
            else:
                state = SyncState(key="dropbox_cursor", value=cursor)
                db.add(state)
            await db.commit()

    async def _clear_cursor(self):
        async with async_session_factory() as db:
            result = await db.execute(
                select(SyncState).where(SyncState.key == "dropbox_cursor")
            )
            state = result.scalar_one_or_none()
            if state:
                await db.delete(state)
                await db.commit()

    async def _process_file(self, client: dropbox.Dropbox, entry: FileMetadata) -> bool:
        async with async_session_factory() as db:
            # Look up by dropbox_id or dropbox_path
            result = await db.execute(
                select(Presentation).where(
                    (Presentation.dropbox_id == entry.id) | 
                    (Presentation.dropbox_path == entry.path_display)
                )
            )
            existing = result.scalar_one_or_none()
            
            # Skip downloading if hash matches
            if existing and existing.dropbox_content_hash == entry.content_hash:
                logger.info(f"File {entry.name} is unchanged (hash matches).")
                if not existing.is_active:
                    existing.is_active = True
                    await db.commit()
                return True

            logger.info(f"Syncing file: {entry.name} ({'modified' if existing else 'new'})")
            
            # Compute relative path inside cache
            rel_path = entry.path_display
            if rel_path.lower().startswith(settings.dropbox_folder_path.lower()):
                rel_path = rel_path[len(settings.dropbox_folder_path):]
            rel_path = rel_path.lstrip('/')
            
            local_path = settings.presentations_path / rel_path
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Log ingestion
            log_entry = IngestionLog(file_path=str(local_path), status="processing")
            db.add(log_entry)
            await db.flush()

            try:
                # Download from Dropbox
                await asyncio.to_thread(
                    client.files_download_to_file,
                    str(local_path),
                    entry.path_lower
                )
                
                # Verify file and compute local hash
                file_hash = compute_file_hash(local_path)
                log_entry.file_hash = file_hash
                
                # Metadata extraction
                metadata = extract_metadata(local_path)
                title = metadata.get("title") or title_from_filename(entry.name)
                
                # Generate WebP thumbnail
                thumbnail_path = generate_thumbnail(local_path, settings.thumbnails_path)
                
                # Reading time estimation
                slide_count = metadata.get("slide_count")
                reading_time = None
                if slide_count:
                    reading_time = max(1, slide_count * 2)
                elif entry.name.lower().endswith(".pdf"):
                    reading_time = max(1, slide_count or 1)
                
                # Text extraction for index & search
                extracted_content = extract_full_content(local_path)
                
                if existing:
                    # Update metadata
                    existing.title = title
                    existing.description = metadata.get("description") or existing.description
                    existing.file_name = entry.name
                    existing.file_path = str(local_path)
                    existing.file_size = entry.size
                    existing.file_hash = file_hash
                    existing.dropbox_id = entry.id
                    existing.dropbox_path = entry.path_display
                    existing.dropbox_content_hash = entry.content_hash
                    existing.slide_count = slide_count or existing.slide_count
                    existing.reading_time_minutes = reading_time or existing.reading_time_minutes
                    existing.thumbnail_path = str(thumbnail_path) if thumbnail_path else existing.thumbnail_path
                    existing.author = metadata.get("author") or existing.author
                    existing.file_modified_at = entry.client_modified
                    existing.updated_at = datetime.utcnow()
                    existing.extracted_text = extracted_content.text
                    existing.content_hash = extracted_content.content_hash
                    existing.is_active = True
                    
                    pres_id = str(existing.id)
                else:
                    # Insert new record
                    pres = Presentation(
                        title=title,
                        description=metadata.get("description"),
                        file_name=entry.name,
                        file_path=str(local_path),
                        file_type=Path(entry.name).suffix.lower().lstrip('.'),
                        file_size=entry.size,
                        file_hash=file_hash,
                        dropbox_id=entry.id,
                        dropbox_path=entry.path_display,
                        dropbox_content_hash=entry.content_hash,
                        slide_count=slide_count,
                        reading_time_minutes=reading_time,
                        thumbnail_path=str(thumbnail_path) if thumbnail_path else None,
                        author=metadata.get("author"),
                        version="1.0",
                        file_modified_at=entry.client_modified,
                        extracted_text=extracted_content.text,
                        content_hash=extracted_content.content_hash,
                        is_active=True
                    )
                    
                    # Auto-tag
                    auto_tags = extract_auto_tags(entry.name)
                    for tag_name in auto_tags:
                        tag = await get_or_create_tag(db, tag_name)
                        pres.tags.append(tag)
                        
                    db.add(pres)
                    await db.flush()
                    pres_id = str(pres.id)
                
                # Check for category / department auto-mapping from path structure
                path_parts = Path(rel_path).parts
                if len(path_parts) > 1:
                    dept_name = path_parts[0]
                    from app.models.department import Department
                    dept_res = await db.execute(select(Department).where(Department.name.ilike(dept_name)))
                    dept = dept_res.scalar_one_or_none()
                    if not dept:
                        dept = Department(name=dept_name)
                        db.add(dept)
                        await db.flush()
                    
                    pres_obj = existing or pres
                    pres_obj.department_id = dept.id
                    
                log_entry.status = "success"
                log_entry.completed_at = datetime.utcnow()
                await db.commit()
                
                # Pre-convert PPTX to PDF in background
                if entry.name.lower().endswith(".pptx"):
                    from app.services.pdf_converter import preconvert_presentation_by_id
                    asyncio.create_task(preconvert_presentation_by_id(pres_id, str(local_path)))
                
                # Trigger AI classification in background
                if settings.classification_auto_enabled:
                    from app.ingestion.scanner import _classify_in_background
                    asyncio.create_task(_classify_in_background(UUID(pres_id)))
                    
                return True
                
            except Exception as e:
                log_entry.status = "failed"
                log_entry.error_message = str(e)
                log_entry.completed_at = datetime.utcnow()
                await db.commit()
                logger.error(f"Failed to ingest {entry.name} from Dropbox: {e}")
                return False

    async def _process_deletion(self, entry: DeletedMetadata) -> bool:
        async with async_session_factory() as db:
            result = await db.execute(
                select(Presentation).where(
                    (Presentation.dropbox_path == entry.path_display) |
                    (Presentation.dropbox_path.ilike(entry.path_display))
                )
            )
            pres = result.scalar_one_or_none()
            if pres:
                pres.is_active = False
                # If cached file exists, we can clean it up
                if pres.file_path and Path(pres.file_path).exists():
                    try:
                        Path(pres.file_path).unlink()
                    except OSError:
                        pass
                await db.commit()
                logger.info(f"Deactivated deleted presentation: {entry.name}")
                return True
            return False

    def get_status(self) -> dict:
        """Get the current sync service status."""
        return {
            "is_running": self.is_running,
            "last_scan_at": self.last_sync_at.timestamp() if self.last_sync_at else None,
            "files_processed": self.files_processed,
            "files_failed": self.files_failed,
            "watch_paths": [settings.dropbox_folder_path],
            "sync_status": self.sync_status,
            "last_error": self.last_error,
        }


# Global sync service instance
dropbox_sync_service = DropboxSyncService()
