"""Classification API schemas — request/response models for AI classification endpoints."""

from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════
# Response Schemas
# ═══════════════════════════════════════════════════════════════

class ClassificationDetail(BaseModel):
    """Full AI classification detail for a presentation."""
    presentation_id: UUID
    category: Optional[str] = None
    sub_category: Optional[str] = None
    department: Optional[str] = None
    business_domain: Optional[str] = None
    difficulty_level: Optional[str] = None
    confidence_category: Optional[float] = None
    confidence_department: Optional[float] = None
    classification_status: str = "pending"
    tags: list[str] = Field(default_factory=list)
    provider: Optional[str] = None


class SummaryResponse(BaseModel):
    """AI-generated summaries at multiple detail levels."""
    presentation_id: UUID
    short_summary: Optional[str] = None
    medium_summary: Optional[str] = None
    executive_summary: Optional[str] = None
    learning_objectives: list[str] = Field(default_factory=list)
    key_topics: list[str] = Field(default_factory=list)
    generated_by: Optional[str] = None


class KeywordItem(BaseModel):
    """A single extracted keyword."""
    keyword: str
    keyword_type: str
    relevance_score: float = 0.0


class KeywordResponse(BaseModel):
    """Keywords extracted from a presentation, grouped by type."""
    presentation_id: UUID
    keywords: list[KeywordItem] = Field(default_factory=list)
    total: int = 0


class SimilarPresentationItem(BaseModel):
    """A presentation similar to the queried one."""
    id: UUID
    title: str
    file_type: str
    thumbnail_url: Optional[str] = None
    similarity_score: float = 0.0
    similarity_type: str = "content"
    category: Optional[str] = None


class SimilarPresentationsResponse(BaseModel):
    """List of similar presentations."""
    presentation_id: UUID
    similar: list[SimilarPresentationItem] = Field(default_factory=list)


class RecommendationSet(BaseModel):
    """Full recommendation set for a presentation."""
    presentation_id: UUID
    similar: list[SimilarPresentationItem] = Field(default_factory=list)
    trending: list[dict] = Field(default_factory=list)
    new_in_domain: list[dict] = Field(default_factory=list)


class QualityScores(BaseModel):
    """Quality metrics for a presentation."""
    completeness_score: Optional[float] = None
    freshness_score: Optional[float] = None
    knowledge_score: Optional[float] = None
    popularity_score: float = 0.0
    overall_score: Optional[float] = None


# ═══════════════════════════════════════════════════════════════
# Request Schemas
# ═══════════════════════════════════════════════════════════════

class ReviewRequest(BaseModel):
    """Admin review action for an AI classification."""
    action: str = Field(..., pattern="^(accepted|modified|rejected)$")
    reviewer: str = "admin"
    final_category_id: Optional[UUID] = None
    final_tag_ids: Optional[list[UUID]] = None
    notes: Optional[str] = None


class ReclassifyRequest(BaseModel):
    """Request to force re-classification."""
    force: bool = True


# ═══════════════════════════════════════════════════════════════
# Admin Dashboard Schemas
# ═══════════════════════════════════════════════════════════════

class ClassificationQueueItem(BaseModel):
    """Presentation awaiting admin review."""
    id: UUID
    title: str
    file_type: str
    thumbnail_url: Optional[str] = None
    ai_category: Optional[str] = None
    ai_confidence: Optional[float] = None
    tags: list[str] = Field(default_factory=list)
    classification_status: str
    created_at: datetime


class ClassificationStats(BaseModel):
    """Dashboard statistics for the classification system."""
    total_presentations: int = 0
    by_status: dict = Field(default_factory=dict)
    average_confidence: float = 0.0
