"""Score model for content quality scores."""

from typing import TYPE_CHECKING

from sqlalchemy import DECIMAL, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.content import Content


class Score(Base):
    """Content quality scores (heat, potential, etc.)."""
    
    __tablename__ = "scores"
    
    content_id: Mapped[int] = mapped_column(
        ForeignKey("contents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    score: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=False)
    factors: Mapped[dict] = mapped_column(JSONB, default=dict)
    algorithm_version: Mapped[str] = mapped_column(String(20), default="1.0")
    
    # Relationships
    content: Mapped["Content"] = relationship("Content", back_populates="scores")
    
    __table_args__ = (
        UniqueConstraint("content_id", "score_type", name="uq_score_content_type"),
    )
    
    def __repr__(self) -> str:
        return f"<Score(id={self.id}, content_id={self.content_id}, type='{self.score_type}', score={self.score})>"
