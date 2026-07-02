"""Synchronization state tracking model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text

from app.database import Base


class SyncState(Base):
    """Stores key-value state for synchronizations (e.g. Dropbox cursors)."""

    __tablename__ = "sync_state"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SyncState(key='{self.key}', value='{self.value[:30]}...', updated_at={self.updated_at})>"
