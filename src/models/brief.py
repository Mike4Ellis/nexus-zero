"""Daily brief model for generated briefings."""

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class DailyBrief(Base):
    """Daily briefing generated from curated content."""
    
    __tablename__ = "daily_briefs"
    
    brief_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Statistics
    stats: Mapped[dict] = mapped_column(JSONB, default=dict)
    total_contents: Mapped[int] = mapped_column(Integer, default=0)
    
    # Content composition
    featured_ids: Mapped[List[int]] = mapped_column(JSONB, default=list)
    heat_top_ids: Mapped[List[int]] = mapped_column(JSONB, default=list)
    potential_ids: Mapped[List[int]] = mapped_column(JSONB, default=list)
    
    # Generated content
    markdown_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    html_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Delivery status
    telegram_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<DailyBrief(id={self.id}, date='{self.brief_date}', title='{self.title[:30]}...')>"
