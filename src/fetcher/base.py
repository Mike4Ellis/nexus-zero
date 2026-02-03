"""Base fetcher class for all content sources."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.models.content import Content
from src.models.log import FetchLog
from src.models.source import Source


class FetchResult:
    """Result of a fetch operation."""
    
    def __init__(
        self,
        items: List[Dict[str, Any]],
        total_fetched: int = 0,
        new_items: int = 0,
        updated_items: int = 0,
        error: Optional[str] = None,
    ):
        self.items = items
        self.total_fetched = total_fetched
        self.new_items = new_items
        self.updated_items = updated_items
        self.error = error
        self.success = error is None


class BaseFetcher(ABC):
    """Abstract base class for content fetchers."""
    
    def __init__(self, source: Source, db: Session):
        self.source = source
        self.db = db
        self.platform = self.get_platform()
    
    @abstractmethod
    def get_platform(self) -> str:
        """Return the platform identifier (e.g., 'x', 'reddit', 'rss')."""
        raise NotImplementedError
    
    @abstractmethod
    def fetch(self, since: Optional[datetime] = None) -> FetchResult:
        """Fetch content from the source.
        
        Args:
            since: Only fetch content newer than this datetime
            
        Returns:
            FetchResult with items and metadata
        """
        raise NotImplementedError
    
    @abstractmethod
    def parse_item(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse raw API data into standardized content format.
        
        Returns:
            Dict with standardized fields or None if invalid
        """
        raise NotImplementedError
    
    def save_items(self, items: List[Dict[str, Any]]) -> int:
        """Save parsed items to database.
        
        Returns:
            Number of new items saved
        """
        new_count = 0
        
        for item_data in items:
            # Check for duplicates
            existing = self.db.query(Content).filter(
                Content.platform == self.platform,
                Content.external_id == item_data["external_id"],
            ).first()
            
            if existing:
                # Update existing content metrics
                existing.raw_metrics = item_data.get("raw_metrics", {})
                existing.updated_at = datetime.utcnow()
            else:
                # Create new content
                content = Content(
                    source_id=self.source.id,
                    platform=self.platform,
                    external_id=item_data["external_id"],
                    title=item_data.get("title"),
                    content=item_data["content"],
                    author=item_data.get("author"),
                    author_id=item_data.get("author_id"),
                    url=item_data.get("url"),
                    published_at=item_data["published_at"],
                    raw_metrics=item_data.get("raw_metrics", {}),
                    media_urls=item_data.get("media_urls", []),
                )
                self.db.add(content)
                new_count += 1
        
        self.db.commit()
        return new_count
    
    def log_fetch(
        self,
        status: str,
        items_fetched: int = 0,
        items_new: int = 0,
        error_message: Optional[str] = None,
    ) -> FetchLog:
        """Log fetch operation for monitoring."""
        log = FetchLog(
            source_id=self.source.id,
            platform=self.platform,
            status=status,
            items_fetched=items_fetched,
            items_new=items_new,
            error_message=error_message,
        )
        self.db.add(log)
        self.db.commit()
        return log
    
    def run(self, since: Optional[datetime] = None) -> FetchResult:
        """Execute full fetch workflow."""
        # Create initial log entry
        self.log_fetch(status="running")
        
        try:
            # Fetch data
            result = self.fetch(since)
            
            if not result.success:
                self.log_fetch(
                    status="failed",
                    error_message=result.error,
                )
                return result
            
            # Parse and save items
            parsed_items = []
            for item in result.items:
                parsed = self.parse_item(item)
                if parsed:
                    parsed_items.append(parsed)
            
            new_count = self.save_items(parsed_items)
            
            # Update source last_fetch_at
            self.source.last_fetch_at = datetime.utcnow().isoformat()
            self.db.commit()
            
            # Log success
            self.log_fetch(
                status="success",
                items_fetched=result.total_fetched,
                items_new=new_count,
            )
            
            return FetchResult(
                items=parsed_items,
                total_fetched=result.total_fetched,
                new_items=new_count,
            )
            
        except Exception as e:
            error_msg = str(e)
            self.log_fetch(
                status="failed",
                error_message=error_msg,
            )
            return FetchResult(
                items=[],
                error=error_msg,
            )
