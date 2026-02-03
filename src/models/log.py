"""Fetch log model for tracking fetcher operations."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.source import Source


class FetchLog(Base):
    """Log of fetch operations for monitoring and debugging."""
    
    __tablename__ = "fetch_logs"
    
    source_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sources.id"),
        nullable=True,
        index=True,
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Execution info
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # running, success, failed, partial
    
    # Results
    items_fetched: Mapped[int] = mapped_column(Integer, default=0)
    items_new: Mapped[int] = mapped_column(Integer, default=0)
    items_updated: Mapped[int] = mapped_column(Integer, default=0)
    
    # Error info
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Debug info
    request_params: Mapped[dict] = mapped_column(JSONB, default=dict)
    response_meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Relationships
    source: Mapped[Optional["Source"]] = relationship("Source", back_populates="fetch_logs")
    
    def __repr__(self) -> str:
        return f"<FetchLog(id={self.id}, platform='{self.platform}', status='{self.status}', items_new={self.items_new})>"
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate fetch duration in seconds."""
        if self.ended_at and self.started_at:
            return (self.ended_at - self.started_at).total_seconds()
        return None
