"""Ingestion log model for tracking file processing."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class IngestionLog(Base):
    """Audit log for the auto-ingestion engine."""

    __tablename__ = "ingestion_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_path = Column(String(1000), nullable=False)
    status = Column(String(20), nullable=False)  # success, failed, skipped
    error_message = Column(Text, nullable=True)
    file_hash = Column(String(64), nullable=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<IngestionLog(file='{self.file_path}', status='{self.status}')>"
