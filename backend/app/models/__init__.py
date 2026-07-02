"""SQLAlchemy ORM models."""

from app.models.presentation import Presentation, PresentationTag
from app.models.category import Category
from app.models.department import Department
from app.models.tag import Tag
from app.models.analytics import ViewHistory, SearchHistory, Bookmark
from app.models.offline import OfflineSync
from app.models.ingestion import IngestionLog
from app.models.sync_state import SyncState
from app.models.ai_classification import (
    AISummary, AIKeyword, PresentationSimilarity, ClassificationReview,
)

__all__ = [
    "Presentation",
    "PresentationTag",
    "Category",
    "Department",
    "Tag",
    "ViewHistory",
    "SearchHistory",
    "Bookmark",
    "OfflineSync",
    "IngestionLog",
    "SyncState",
    "AISummary",
    "AIKeyword",
    "PresentationSimilarity",
    "ClassificationReview",
]
