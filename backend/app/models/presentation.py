"""Presentation ORM model — the core entity."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, BigInteger,
    String, Text, Index, Table
)
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import relationship

from app.database import Base


# Many-to-many junction table
PresentationTag = Table(
    "presentation_tags",
    Base.metadata,
    Column("presentation_id", UUID(as_uuid=True), ForeignKey("presentations.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Presentation(Base):
    """Core presentation entity representing a single file in the knowledge portal."""

    __tablename__ = "presentations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=True, unique=True)
    file_type = Column(String(20), nullable=False, index=True)  # pptx, pdf, html
    file_size = Column(BigInteger, nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True)  # SHA-256
    dropbox_id = Column(String(100), nullable=True, unique=True, index=True)
    dropbox_path = Column(String(1000), nullable=True, unique=True, index=True)
    dropbox_content_hash = Column(String(64), nullable=True)
    slide_count = Column(Integer, nullable=True)
    reading_time_minutes = Column(Integer, nullable=True)
    thumbnail_path = Column(String(1000), nullable=True)

    # Relationships
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True, index=True)

    # Metadata
    author = Column(String(255), nullable=True)
    version = Column(String(50), nullable=True, default="1.0")

    # AI Classification
    ai_category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True)
    ai_department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True, index=True)
    ai_confidence_category = Column(Float, nullable=True)       # 0.0–1.0
    ai_confidence_department = Column(Float, nullable=True)     # 0.0–1.0
    ai_classification_status = Column(
        String(20), nullable=False, default="pending",
        index=True,
    )  # pending, classified, reviewed, rejected
    difficulty_level = Column(String(20), nullable=True)        # beginner, intermediate, advanced, expert
    business_domain = Column(String(100), nullable=True)

    # Content for search / similarity
    extracted_text = Column(Text, nullable=True)                # Full extracted text
    content_hash = Column(String(64), nullable=True)            # Hash of extracted text

    # Quality Scores
    completeness_score = Column(Float, nullable=True)
    freshness_score = Column(Float, nullable=True)
    knowledge_score = Column(Float, nullable=True)

    # Analytics
    view_count = Column(Integer, nullable=False, default=0)
    download_count = Column(Integer, nullable=False, default=0)
    popularity_score = Column(Float, nullable=False, default=0.0)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    file_modified_at = Column(DateTime, nullable=True)
    last_viewed_at = Column(DateTime, nullable=True)

    # Search
    search_vector = Column(TSVECTOR, nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)

    # ORM relationships
    category = relationship(
        "Category", back_populates="presentations", lazy="selectin",
        foreign_keys=[category_id],
    )
    ai_category = relationship(
        "Category", lazy="selectin",
        foreign_keys=[ai_category_id],
    )
    department = relationship(
        "Department", back_populates="presentations", lazy="selectin",
        foreign_keys=[department_id],
    )
    ai_department = relationship(
        "Department", lazy="selectin",
        foreign_keys=[ai_department_id],
    )
    tags = relationship("Tag", secondary=PresentationTag, back_populates="presentations", lazy="selectin")
    bookmarks = relationship("Bookmark", back_populates="presentation", cascade="all, delete-orphan")
    view_history = relationship("ViewHistory", back_populates="presentation", cascade="all, delete-orphan")
    offline_syncs = relationship("OfflineSync", back_populates="presentation", cascade="all, delete-orphan")

    # AI relationships
    ai_summary = relationship("AISummary", back_populates="presentation", uselist=False, cascade="all, delete-orphan")
    ai_keywords = relationship("AIKeyword", back_populates="presentation", cascade="all, delete-orphan")
    similar_from = relationship(
        "PresentationSimilarity", back_populates="source",
        foreign_keys="PresentationSimilarity.source_id", cascade="all, delete-orphan",
    )
    similar_to = relationship(
        "PresentationSimilarity", back_populates="target",
        foreign_keys="PresentationSimilarity.target_id", cascade="all, delete-orphan",
    )
    classification_reviews = relationship(
        "ClassificationReview", back_populates="presentation", cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_pres_search", "search_vector", postgresql_using="gin"),
        Index("idx_pres_popularity", popularity_score.desc()),
        Index("idx_pres_created", created_at.desc()),
        Index("idx_pres_updated", updated_at.desc()),
        Index("idx_trgm_title", "title", postgresql_using="gin", postgresql_ops={"title": "gin_trgm_ops"}),
        Index("idx_pres_ai_status", "ai_classification_status"),
    )

    def __repr__(self):
        return f"<Presentation(id={self.id}, title='{self.title}', type='{self.file_type}')>"
