"""Application configuration via Pydantic Settings."""

from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "SlideVault"
    app_version: str = "1.0.0"
    debug: bool = False
    api_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+asyncpg://slidevault:slidevault@localhost:5432/slidevault"
    database_echo: bool = False

    # Storage
    presentations_dir: str = r"D:\Gamma Slides\PPT"
    thumbnails_dir: str = r"D:\Gamma Slides\slidevault\storage\thumbnails"
    cache_dir: str = r"D:\Gamma Slides\slidevault\storage\cache"

    # Dropbox
    dropbox_app_key: str = ""
    dropbox_app_secret: str = ""
    dropbox_refresh_token: str = ""
    dropbox_folder_path: str = "/Presentations"
    dropbox_sync_interval_seconds: int = 300

    # Ingestion
    watch_interval_seconds: int = 30
    supported_extensions: str = ".pptx,.pdf,.html"
    thumbnail_width: int = 640
    thumbnail_height: int = 360
    thumbnail_quality: int = 85

    # Search
    search_min_score: float = 0.1
    search_max_results: int = 100
    fuzzy_threshold: float = 0.3

    # Pagination
    default_page_size: int = 24
    max_page_size: int = 100

    # AI Provider
    ai_provider: str = "rule_based"   # rule_based, openai, claude, gemini, ollama
    ai_model: str = ""                # Model name for API-based providers
    ai_api_key: str = ""              # API key (if needed)
    ai_base_url: str = ""             # Custom endpoint (e.g., Ollama)

    # Classification
    classification_auto_enabled: bool = True
    classification_confidence_threshold: float = 0.7  # Below this → requires review
    classification_max_tags: int = 20
    classification_min_tags: int = 5

    # Quality Scoring Weights
    quality_completeness_weight: float = 0.3
    quality_freshness_weight: float = 0.2
    quality_popularity_weight: float = 0.3
    quality_knowledge_weight: float = 0.2

    # Similarity
    similarity_threshold: float = 0.3
    similarity_max_results: int = 10

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:80"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 2

    @property
    def presentations_path(self) -> Path:
        return Path(self.presentations_dir)

    @property
    def thumbnails_path(self) -> Path:
        path = Path(self.thumbnails_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def cache_path(self) -> Path:
        path = Path(self.cache_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def supported_extensions_list(self) -> list[str]:
        return [ext.strip() for ext in self.supported_extensions.split(",")]

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = {"env_prefix": "SLIDEVAULT_", "env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
