"""SlideVault — Presentation Knowledge Portal API.

FastAPI application factory with CORS, lifecycle management, and route registration.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import init_db, close_db
from app.api.presentations import router as presentations_router
from app.api.search import router as search_router
from app.api.categories import router as categories_router
from app.api.analytics import analytics_router, admin_router
from app.api.thumbnails import router as thumbnails_router
from app.api.classification import router as classification_router
from app.api.slide_content import router as slide_content_router
from app.api.classification import admin_classification_router
from app.services.dropbox_sync_service import dropbox_sync_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — init DB, run initial scan, start Dropbox sync service."""
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")

    # Initialize database tables
    await init_db()
    logger.info("✅ Database initialized")

    # Ensure storage directories exist
    settings.thumbnails_path.mkdir(parents=True, exist_ok=True)
    settings.cache_path.mkdir(parents=True, exist_ok=True)

    # Seed category hierarchy if empty
    try:
        from app.seed_categories import seed_categories_if_empty
        await seed_categories_if_empty()
        logger.info("✅ Category hierarchy verified")
    except Exception as e:
        logger.warning(f"⚠️ Category seeding skipped: {e}")

    # Run initial scan of presentations directory from Dropbox
    logger.info(f"📁 Synchronizing presentations from Dropbox path: {settings.dropbox_folder_path}")
    try:
        result = await dropbox_sync_service.sync()
        logger.info(f"📊 Initial Dropbox sync: {result}")
    except Exception as e:
        logger.error(f"❌ Initial Dropbox sync failed: {e}")

    # Classify any pending presentations
    if settings.classification_auto_enabled:
        try:
            from app.services.classification_service import classify_all_pending
            from app.database import async_session_factory
            async with async_session_factory() as db:
                stats = await classify_all_pending(db)
                logger.info(f"🤖 Auto-classification: {stats}")
        except Exception as e:
            logger.warning(f"⚠️ Auto-classification skipped: {e}")

    # Start Dropbox sync service
    await dropbox_sync_service.start()
    logger.info("👁️  Dropbox sync service started")

    yield

    # Shutdown
    logger.info("🛑 Shutting down...")
    await dropbox_sync_service.stop()
    await close_db()
    logger.info("✅ Shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="Enterprise Presentation Knowledge Portal — Centralized discovery, search, and viewing platform for 200+ presentations.",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routes
    prefix = settings.api_prefix
    app.include_router(presentations_router, prefix=prefix)
    app.include_router(search_router, prefix=prefix)
    app.include_router(categories_router, prefix=prefix)
    app.include_router(analytics_router, prefix=prefix)
    app.include_router(admin_router, prefix=prefix)
    app.include_router(thumbnails_router, prefix=prefix)
    app.include_router(classification_router, prefix=prefix)
    app.include_router(admin_classification_router, prefix=prefix)
    app.include_router(slide_content_router, prefix=prefix)

    # Health check
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version,
        }

    # Serve built frontend from ../frontend/dist if it exists (single-port mode)
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

        from fastapi.responses import FileResponse

        @app.get("/")
        async def serve_spa():
            return FileResponse(str(frontend_dist / "index.html"))

        @app.get("/{full_path:path}")
        async def serve_spa_routes(full_path: str):
            # API routes are matched before this catch-all
            file_path = frontend_dist / full_path
            if file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))
            return FileResponse(str(frontend_dist / "index.html"))
    else:
        @app.get("/")
        async def root():
            return {
                "app": settings.app_name,
                "version": settings.app_version,
                "docs": "/api/docs",
                "health": "/health",
            }

    return app


app = create_app()
