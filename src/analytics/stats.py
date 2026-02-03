"""Analytics reporting and export functionality."""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from src.models.content import Content
from src.models.brief import DailyBrief
from src.models.source import Source
from src.models.score import Score


class AnalyticsReporter:
    """Generate analytics reports for Nexus Zero."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_overview_stats(self) -> Dict[str, Any]:
        """Get high-level overview statistics."""
        total_contents = self.db.query(Content).count()
        total_sources = self.db.query(Source).count()
        active_sources = self.db.query(Source).filter(Source.is_active == True).count()
        
        # Content by platform
        platform_stats = (
            self.db.query(Content.platform, func.count(Content.id))
            .group_by(Content.platform)
            .all()
        )
        
        # Content by date (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        daily_counts = (
            self.db.query(
                func.date(Content.published_at),
                func.count(Content.id)
            )
            .filter(Content.published_at >= week_ago)
            .group_by(func.date(Content.published_at))
            .order_by(func.date(Content.published_at))
            .all()
        )
        
        # Average scores
        avg_heat = (
            self.db.query(func.avg(Score.score))
            .filter(Score.score_type == "heat")
            .scalar()
        ) or 0
        
        avg_potential = (
            self.db.query(func.avg(Score.score))
            .filter(Score.score_type == "potential")
            .scalar()
        ) or 0
        
        return {
            "total_contents": total_contents,
            "total_sources": total_sources,
            "active_sources": active_sources,
            "platform_breakdown": {p: c for p, c in platform_stats},
            "daily_counts": [{"date": str(d), "count": c} for d, c in daily_counts],
            "average_scores": {
                "heat": round(float(avg_heat), 2),
                "potential": round(float(avg_potential), 2),
            },
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    def get_platform_analysis(self) -> Dict[str, Any]:
        """Analyze content by platform."""
        platforms = ["x", "reddit", "rss", "xiaohongshu"]
        analysis = {}
        
        for platform in platforms:
            contents = self.db.query(Content).filter(Content.platform == platform)
            
            total = contents.count()
            if total == 0:
                continue
            
            # Get top content by heat score
            top_content = (
                contents.join(Score, Content.id == Score.content_id)
                .filter(Score.score_type == "heat")
                .order_by(Score.score.desc())
                .limit(5)
                .all()
            )
            
            analysis[platform] = {
                "total_contents": total,
                "top_content": [
                    {
                        "id": c.id,
                        "title": c.title or c.content[:100],
                        "author": c.author,
                        "published_at": c.published_at.isoformat() if c.published_at else None,
                    }
                    for c in top_content
                ],
            }
        
        return analysis
    
    def get_trending_topics(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending topics based on recent content."""
        since = datetime.utcnow() - timedelta(days=days)
        
        # This is a simplified implementation
        # In production, you would use NLP to extract topics
        recent_content = (
            self.db.query(Content)
            .filter(Content.published_at >= since)
            .order_by(Content.id.desc())
            .limit(100)
            .all()
        )
        
        # Simple keyword extraction (placeholder)
        keywords = {}
        for content in recent_content:
            text = f"{content.title or ''} {content.content or ''}".lower()
            # Count common tech keywords
            tech_keywords = ["ai", "人工智能", "chatgpt", "crypto", "区块链", "web3", "python", "javascript"]
            for keyword in tech_keywords:
                if keyword in text:
                    keywords[keyword] = keywords.get(keyword, 0) + 1
        
        # Sort by frequency
        sorted_topics = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {"topic": topic, "mentions": count}
            for topic, count in sorted_topics[:limit]
        ]
    
    def generate_report(self, start_date: Optional[datetime] = None, 
                       end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate comprehensive analytics report."""
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "overview": self.get_overview_stats(),
            "platform_analysis": self.get_platform_analysis(),
            "trending_topics": self.get_trending_topics(),
        }


def generate_daily_report(db: Session, date: Optional[datetime] = None) -> Dict[str, Any]:
    """Generate daily report for specific date."""
    if not date:
        date = datetime.utcnow() - timedelta(days=1)
    
    start_of_day = datetime.combine(date.date(), datetime.min.time())
    end_of_day = start_of_day + timedelta(days=1)
    
    reporter = AnalyticsReporter(db)
    
    # Get brief for the day
    brief = (
        db.query(DailyBrief)
        .filter(DailyBrief.brief_date == date.date())
        .first()
    )
    
    # Get content stats
    contents = (
        db.query(Content)
        .filter(
            and_(
                Content.published_at >= start_of_day,
                Content.published_at < end_of_day
            )
        )
        .all()
    )
    
    return {
        "date": date.date().isoformat(),
        "brief": {
            "title": brief.title if brief else None,
            "total_contents": brief.total_contents if brief else len(contents),
            "telegram_sent": brief.telegram_sent if brief else False,
            "email_sent": brief.email_sent if brief else False,
        },
        "new_contents": len(contents),
        "platform_breakdown": reporter.get_overview_stats()["platform_breakdown"],
    }


def export_to_excel(db: Session, output_path: str, 
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> str:
    """Export content data to Excel file.
    
    Args:
        db: Database session
        output_path: Path to save Excel file
        start_date: Filter contents from this date
        end_date: Filter contents until this date
        
    Returns:
        Path to exported file
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas is required for Excel export. Install: pip install pandas openpyxl")
    
    query = db.query(Content)
    
    if start_date:
        query = query.filter(Content.published_at >= start_date)
    if end_date:
        query = query.filter(Content.published_at <= end_date)
    
    contents = query.order_by(Content.published_at.desc()).all()
    
    # Prepare data for DataFrame
    data = []
    for content in contents:
        # Get scores
        heat_score = (
            db.query(Score)
            .filter(Score.content_id == content.id, Score.score_type == "heat")
            .first()
        )
        potential_score = (
            db.query(Score)
            .filter(Score.content_id == content.id, Score.score_type == "potential")
            .first()
        )
        
        data.append({
            "ID": content.id,
            "Platform": content.platform,
            "Title": content.title or content.content[:200],
            "Author": content.author,
            "URL": content.url,
            "Published At": content.published_at,
            "Heat Score": heat_score.score if heat_score else None,
            "Potential Score": potential_score.score if potential_score else None,
            "Likes": content.raw_metrics.get("likes", 0) if content.raw_metrics else 0,
            "Comments": content.raw_metrics.get("comments", 0) if content.raw_metrics else 0,
            "Shares": content.raw_metrics.get("reposts", 0) if content.raw_metrics else 0,
        })
    
    # Create DataFrame and export
    df = pd.DataFrame(data)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    df.to_excel(output_path, index=False, engine="openpyxl")
    
    return output_path


def export_to_json(db: Session, output_path: str,
                  start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None) -> str:
    """Export analytics report to JSON file.
    
    Args:
        db: Database session
        output_path: Path to save JSON file
        start_date: Report start date
        end_date: Report end date
        
    Returns:
        Path to exported file
    """
    reporter = AnalyticsReporter(db)
    report = reporter.generate_report(start_date, end_date)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    return output_path
