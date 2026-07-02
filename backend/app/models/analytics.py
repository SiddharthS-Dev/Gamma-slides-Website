"""Analytics ORM models — ViewHistory, SearchHistory, Bookmark."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ViewHistory(Base):
    """Records each presentation view event for analytics and resume."""

    __tablename__ = "view_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    presentation_id = Column(UUID(as_uuid=True), ForeignKey("presentations.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(100), nullable=True)
    last_slide = Column(Integer, nullable=True)
    total_slides_viewed = Column(Integer, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    viewed_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    presentation = relationship("Presentation", back_populates="view_history")

    def __repr__(self):
        return f"<ViewHistory(presentation_id={self.presentation_id}, viewed_at={self.viewed_at})>"


class SearchHistory(Base):
    """Records search queries for analytics and suggestions."""

    __tablename__ = "search_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query = Column(String(500), nullable=False, index=True)
    result_count = Column(Integer, nullable=True)
    session_id = Column(String(100), nullable=True)
    searched_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<SearchHistory(query='{self.query}', results={self.result_count})>"


class Bookmark(Base):
    """User bookmark on a specific slide within a presentation."""

    __tablename__ = "bookmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    presentation_id = Column(UUID(as_uuid=True), ForeignKey("presentations.id", ondelete="CASCADE"), nullable=False, index=True)
    slide_number = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)
    session_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    presentation = relationship("Presentation", back_populates="bookmarks")

    def __repr__(self):
        return f"<Bookmark(presentation_id={self.presentation_id}, slide={self.slide_number})>"
