"""Content model for fetched content."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.score import Score
    from src.models.source import Source
    from src.models.tag import ContentTag


class Content(Base):
    """Fetched content from various platforms."""
    
    __tablename__ = "contents"
    
    source_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sources.id"),
        nullable=True,
        index=True,
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Content fields
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    author_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    
    # Engagement metrics
    raw_metrics: Mapped[dict] = mapped_column(JSONB, default=dict)
    media_urls: Mapped[list] = mapped_column(JSONB, default=list)
    
    # Processing status
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_briefed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    source: Mapped[Optional["Source"]] = relationship("Source", back_populates="contents")
    scores: Mapped[List["Score"]] = relationship("Score", back_populates="content", cascade="all, delete-orphan")
    content_tags: Mapped[List["ContentTag"]] = relationship("ContentTag", back_populates="content", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("platform", "external_id", name="uq_content_platform_external_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Content(id={self.id}, platform='{self.platform}', external_id='{self.external_id[:20]}...')>"
    
    @property
    def heat_score(self) -> Optional[float]:
        """Get heat score if calculated."""
        for score in self.scores:
            if score.score_type == "heat":
                return float(score.score)
        return None
    
    @property
    def potential_score(self) -> Optional[float]:
        """Get potential score if calculated."""
        for score in self.scores:
            if score.score_type == "potential":
                return float(score.score)
        return None
