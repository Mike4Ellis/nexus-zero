"""Database queries for analytics."""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, desc, and_
from sqlalchemy.orm import Session

from src.models.content import Content
from src.models.source import Source
from src.models.score import Score
from src.models.brief import DailyBrief


class ContentQueries:
    """Queries for content analytics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_total_count(self, platform: Optional[str] = None) -> int:
        """Get total content count, optionally filtered by platform."""
        query = self.db.query(Content)
        if platform:
            query = query.filter(Content.platform == platform)
        return query.count()
    
    def get_daily_counts(self, days: int = 30) -> List[Tuple[date, int]]:
        """Get content counts per day for last N days."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        results = (
            self.db.query(
                func.date(Content.published_at).label("date"),
                func.count(Content.id).label("count")
            )
            .filter(Content.published_at >= start_date)
            .group_by(func.date(Content.published_at))
            .order_by(desc("date"))
            .all()
        )
        
        return [(row.date, row.count) for row in results]
    
    def get_top_content(
        self,
        platform: Optional[str] = None,
        score_type: str = "heat",
        limit: int = 10
    ) -> List[Content]:
        """Get top content by score."""
        query = (
            self.db.query(Content)
            .join(Score)
            .filter(Score.score_type == score_type)
            .order_by(desc(Score.score))
        )
        
        if platform:
            query = query.filter(Content.platform == platform)
        
        return query.limit(limit).all()
    
    def get_platform_distribution(self) -> Dict[str, int]:
        """Get content count by platform."""
        results = (
            self.db.query(Content.platform, func.count(Content.id))
            .group_by(Content.platform)
            .all()
        )
        
        return {platform: count for platform, count in results}


class PlatformQueries:
    """Queries for platform analytics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_active_sources(self) -> List[Source]:
        """Get all active sources."""
        return self.db.query(Source).filter(Source.is_active == True).all()
    
    def get_source_stats(self) -> List[Dict]:
        """Get statistics for each source."""
        sources = self.get_active_sources()
        stats = []
        
        for source in sources:
            content_count = (
                self.db.query(Content)
                .filter(Content.source_id == source.id)
                .count()
            )
            
            latest_content = (
                self.db.query(Content)
                .filter(Content.source_id == source.id)
                .order_by(desc(Content.published_at))
                .first()
            )
            
            stats.append({
                "source_id": source.id,
                "name": source.name,
                "platform": source.platform,
                "content_count": content_count,
                "last_fetch": source.last_fetch_at,
                "latest_content": latest_content.published_at if latest_content else None,
            })
        
        return stats


class TimeSeriesQueries:
    """Queries for time-series analytics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_hourly_distribution(self, target_date: date) -> List[Tuple[int, int]]:
        """Get content distribution by hour for a specific date."""
        start = datetime.combine(target_date, datetime.min.time())
        end = start + timedelta(days=1)
        
        results = (
            self.db.query(
                func.extract('hour', Content.published_at).label("hour"),
                func.count(Content.id).label("count")
            )
            .filter(and_(
                Content.published_at >= start,
                Content.published_at < end
            ))
            .group_by(func.extract('hour', Content.published_at))
            .order_by("hour")
            .all()
        )
        
        return [(int(row.hour), row.count) for row in results]
    
    def get_weekly_trend(self, weeks: int = 4) -> List[Tuple[str, int]]:
        """Get weekly content counts."""
        start_date = datetime.utcnow() - timedelta(weeks=weeks)
        
        results = (
            self.db.query(
                func.strftime('%Y-W%W', Content.published_at).label("week"),
                func.count(Content.id).label("count")
            )
            .filter(Content.published_at >= start_date)
            .group_by(func.strftime('%Y-W%W', Content.published_at))
            .order_by(desc("week"))
            .all()
        )
        
        return [(row.week, row.count) for row in results]
