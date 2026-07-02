"""Tag ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.presentation import PresentationTag


class Tag(Base):
    """Tag for flexible cross-cutting content classification."""

    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    color = Column(String(7), nullable=True, default="#8b5cf6")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    presentations = relationship("Presentation", secondary=PresentationTag, back_populates="tags", lazy="selectin")

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"
