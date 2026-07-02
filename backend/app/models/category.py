"""Category ORM model with hierarchical support."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Category(Base):
    """Presentation category with optional parent for hierarchical organization.

    Example hierarchy:
        Engineering (parent_id=None)
        ├── Architecture (parent_id=Engineering.id)
        ├── Backend
        ├── Frontend
        └── DevOps
    """

    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True, default="#6366f1")  # Hex color
    icon = Column(String(50), nullable=True, default="folder")
    sort_order = Column(Integer, nullable=False, default=0)
    presentation_count = Column(Integer, nullable=False, default=0)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Self-referencing hierarchy
    parent = relationship("Category", remote_side="Category.id", backref="sub_categories")

    # Relationships
    presentations = relationship(
        "Presentation", back_populates="category", lazy="selectin",
        foreign_keys="Presentation.category_id",
    )

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', parent_id={self.parent_id})>"
