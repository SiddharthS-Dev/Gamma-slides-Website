"""Department ORM model with self-referencing hierarchy."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Department(Base):
    """Department / Business Unit for hierarchical organization."""

    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Self-referencing relationship for hierarchy
    parent = relationship("Department", remote_side="Department.id", backref="children")
    presentations = relationship(
        "Presentation",
        back_populates="department",
        lazy="selectin",
        foreign_keys="Presentation.department_id",
    )

    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}')>"
