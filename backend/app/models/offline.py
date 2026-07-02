"""Offline sync tracking model."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, BigInteger, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class OfflineSync(Base):
    """Tracks which presentations have been downloaded for offline use."""

    __tablename__ = "offline_sync"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    presentation_id = Column(UUID(as_uuid=True), ForeignKey("presentations.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(100), nullable=True)
    sync_status = Column(String(20), nullable=False, default="synced")  # synced, pending, failed
    cached_size = Column(BigInteger, nullable=True)
    synced_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    presentation = relationship("Presentation", back_populates="offline_syncs")

    def __repr__(self):
        return f"<OfflineSync(presentation_id={self.presentation_id}, status='{self.sync_status}')>"
