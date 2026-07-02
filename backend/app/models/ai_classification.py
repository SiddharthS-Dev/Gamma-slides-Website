"""AI classification ORM models — AISummary, AIKeyword, PresentationSimilarity, ClassificationReview."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class AISummary(Base):
    """AI-generated summaries at multiple detail levels for a presentation."""

    __tablename__ = "ai_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    presentation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("presentations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    short_summary = Column(Text, nullable=True)          # ~100 words
    medium_summary = Column(Text, nullable=True)         # ~300 words
    executive_summary = Column(Text, nullable=True)      # Strategic overview
    learning_objectives = Column(Text, nullable=True)    # JSON array
    key_topics = Column(Text, nullable=True)             # JSON array
    generated_by = Column(String(50), nullable=False, default="rule_based")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    presentation = relationship("Presentation", back_populates="ai_summary", uselist=False)

    def __repr__(self):
        return f"<AISummary(presentation_id={self.presentation_id}, by='{self.generated_by}')>"


class AIKeyword(Base):
    """AI-extracted keyword with type classification and relevance score."""

    __tablename__ = "ai_keywords"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    presentation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("presentations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    keyword = Column(String(200), nullable=False)
    keyword_type = Column(String(50), nullable=False, default="concept")  # technology, product, department, etc.
    relevance_score = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    presentation = relationship("Presentation", back_populates="ai_keywords")

    __table_args__ = (
        Index("idx_keyword_type", "keyword_type"),
        Index("idx_keyword_presentation", "presentation_id", "keyword"),
    )

    def __repr__(self):
        return f"<AIKeyword(keyword='{self.keyword}', type='{self.keyword_type}', score={self.relevance_score})>"


class PresentationSimilarity(Base):
    """Similarity relationship between two presentations."""

    __tablename__ = "presentation_similarities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("presentations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_id = Column(
        UUID(as_uuid=True),
        ForeignKey("presentations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    similarity_score = Column(Float, nullable=False, default=0.0)
    similarity_type = Column(String(30), nullable=False, default="content")  # content, topic, successor, duplicate
    computed_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    source = relationship("Presentation", foreign_keys=[source_id], back_populates="similar_from")
    target = relationship("Presentation", foreign_keys=[target_id], back_populates="similar_to")

    __table_args__ = (
        Index("idx_similarity_source_score", "source_id", similarity_score.desc()),
        Index("idx_similarity_pair", "source_id", "target_id", unique=True),
    )

    def __repr__(self):
        return f"<PresentationSimilarity(source={self.source_id}, target={self.target_id}, score={self.similarity_score})>"


class ClassificationReview(Base):
    """Admin review audit log for AI classifications."""

    __tablename__ = "classification_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    presentation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("presentations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer = Column(String(255), nullable=True)
    action = Column(String(20), nullable=False)  # accepted, modified, rejected
    original_category_id = Column(UUID(as_uuid=True), nullable=True)
    final_category_id = Column(UUID(as_uuid=True), nullable=True)
    original_tags = Column(Text, nullable=True)   # JSON array
    final_tags = Column(Text, nullable=True)       # JSON array
    notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    presentation = relationship("Presentation", back_populates="classification_reviews")

    def __repr__(self):
        return f"<ClassificationReview(presentation_id={self.presentation_id}, action='{self.action}')>"
