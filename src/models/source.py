"""Source model for content sources configuration."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.content import Content
    from src.models.log import FetchLog


class Source(Base):
    """Content source configuration."""
    
    __tablename__ = "sources"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    fetch_interval: Mapped[int] = mapped_column(Integer, default=240)  # minutes
    last_fetch_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Relationships
    contents: Mapped[List["Content"]] = relationship("Content", back_populates="source")
    fetch_logs: Mapped[List["FetchLog"]] = relationship("FetchLog", back_populates="source")
    
    def __repr__(self) -> str:
        return f"<Source(id={self.id}, name='{self.name}', platform='{self.platform}')>"
