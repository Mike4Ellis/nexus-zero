"""Tag models for content classification."""

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.content import Content


class Tag(Base):
    """Tag definition for content classification."""
    
    __tablename__ = "tags"
    
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=True, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    color: Mapped[str] = mapped_column(String(7), nullable=True)  # #RRGGBB
    is_auto: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    content_tags: Mapped[List["ContentTag"]] = relationship("ContentTag", back_populates="tag")
    
    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name='{self.name}', category='{self.category}')>"


class ContentTag(Base):
    """Association table between Content and Tag."""
    
    __tablename__ = "content_tags"
    
    content_id: Mapped[int] = mapped_column(
        ForeignKey("contents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    confidence: Mapped[float] = mapped_column(default=1.0)
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    # Relationships
    content: Mapped["Content"] = relationship("Content", back_populates="content_tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="content_tags")
    
    __table_args__ = (
        UniqueConstraint("content_id", "tag_id", name="uq_content_tag"),
    )
    
    def __repr__(self) -> str:
        return f"<ContentTag(content_id={self.content_id}, tag_id={self.tag_id}, confidence={self.confidence})>"
