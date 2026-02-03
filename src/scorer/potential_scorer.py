"""Potential score calculation for discovering hidden gems."""

from datetime import datetime, timezone
from typing import Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.content import Content
from src.models.score import Score
from src.scorer.base import BaseScorer, ScoreResult


class PotentialScorer(BaseScorer):
    """Calculates potential score to identify high-quality but under-discovered content.
    
    Potential Score Formula:
    - Content quality (text analysis)
    - Author historical performance
    - Engagement rate (interactions / views)
    - Growth trend (velocity of engagement)
    - Domain/topic scarcity
    """
    
    # Component weights
    COMPONENT_WEIGHTS = {
        "content_quality": 0.30,
        "author_weight": 0.20,
        "engagement_rate": 0.25,
        "growth_trend": 0.15,
        "scarcity": 0.10,
    }
    
    def __init__(self, db: Session):
        super().__init__(db)
        self._author_cache: Dict[str, float] = {}
    
    def get_score_type(self) -> str:
        return "potential"
    
    def calculate(self, content: Content) -> ScoreResult:
        """Calculate potential score for content."""
        try:
            # Calculate each component
            content_quality = self._calculate_content_quality(content)
            author_weight = self._calculate_author_weight(content)
            engagement_rate = self._calculate_engagement_rate(content)
            growth_trend = self._calculate_growth_trend(content)
            scarcity = self._calculate_scarcity(content)
            
            # Weighted sum
            potential_score = (
                content_quality * self.COMPONENT_WEIGHTS["content_quality"] +
                author_weight * self.COMPONENT_WEIGHTS["author_weight"] +
                engagement_rate * self.COMPONENT_WEIGHTS["engagement_rate"] +
                growth_trend * self.COMPONENT_WEIGHTS["growth_trend"] +
                scarcity * self.COMPONENT_WEIGHTS["scarcity"]
            )
            
            # Normalize to 0-100
            normalized_score = min(100.0, max(0.0, potential_score))
            
            return ScoreResult(
                score=round(normalized_score, 2),
                factors={
                    "content_quality": round(content_quality, 2),
                    "author_weight": round(author_weight, 2),
                    "engagement_rate": round(engagement_rate, 2),
                    "growth_trend": round(growth_trend, 2),
                    "scarcity": round(scarcity, 2),
                },
            )
            
        except Exception as e:
            return ScoreResult(
                score=0.0,
                factors={"error": str(e)},
                success=False,
                error=str(e),
            )
    
    def _calculate_content_quality(self, content: Content) -> float:
        """Estimate content quality based on text characteristics.
        
        Factors:
        - Length (not too short, not too long)
        - Has meaningful structure
        - Contains URLs/media (indicates richness)
        """
        score = 50.0  # Base score
        
        text = content.content or ""
        text_length = len(text)
        
        # Length scoring (optimal: 200-2000 chars)
        if 200 <= text_length <= 2000:
            score += 20
        elif 100 <= text_length < 200:
            score += 10
        elif text_length > 2000:
            score += 15  # Long but might be valuable
        elif text_length < 50:
            score -= 20  # Too short
        
        # Has title
        if content.title and len(content.title) > 10:
            score += 10
        
        # Has media (indicates richer content)
        if content.media_urls and len(content.media_urls) > 0:
            score += 10
        
        # Has URL in content (indicates references)
        if "http" in text:
            score += 5
        
        return min(100.0, score)
    
    def _calculate_author_weight(self, content: Content) -> float:
        """Calculate author historical performance weight.
        
        Based on author's previous content average scores.
        """
        if not content.author_id:
            return 50.0  # Neutral for unknown authors
        
        # Check cache
        cache_key = f"{content.platform}:{content.author_id}"
        if cache_key in self._author_cache:
            return self._author_cache[cache_key]
        
        # Query author's historical performance
        author_scores = self.db.query(Score.score).join(Content).filter(
            Content.platform == content.platform,
            Content.author_id == content.author_id,
            Content.id != content.id,  # Exclude current content
        ).all()
        
        if not author_scores:
            # New author, neutral score with slight bonus for being new
            weight = 55.0
        else:
            # Calculate average score
            avg_score = sum(s[0] for s in author_scores) / len(author_scores)
            # Normalize to 0-100 range
            weight = min(100.0, max(0.0, avg_score))
        
        # Cache result
        self._author_cache[cache_key] = weight
        
        return weight
    
    def _calculate_engagement_rate(self, content: Content) -> float:
        """Calculate engagement rate (interactions per view).
        
        High engagement rate indicates sticky content.
        """
        metrics = content.raw_metrics or {}
        
        views = metrics.get("views", 0)
        likes = metrics.get("likes", 0)
        comments = metrics.get("comments", 0)
        reposts = metrics.get("reposts", 0)
        bookmarks = metrics.get("bookmarks", 0)
        
        total_engagement = likes + comments * 2 + reposts * 3 + bookmarks * 2
        
        if views == 0:
            # No view data, use absolute engagement
            if total_engagement > 100:
                return 70.0
            elif total_engagement > 50:
                return 60.0
            elif total_engagement > 10:
                return 50.0
            else:
                return 40.0
        
        # Calculate rate
        engagement_rate = total_engagement / views
        
        # Convert to score (typical good rate is 0.05-0.15)
        if engagement_rate > 0.20:
            return 90.0
        elif engagement_rate > 0.15:
            return 80.0
        elif engagement_rate > 0.10:
            return 70.0
        elif engagement_rate > 0.05:
            return 60.0
        elif engagement_rate > 0.02:
            return 50.0
        else:
            return 40.0
    
    def _calculate_growth_trend(self, content: Content) -> float:
        """Calculate growth trend based on content age vs engagement.
        
        Fast accumulation of engagement indicates viral potential.
        """
        if not content.published_at:
            return 50.0
        
        # Ensure timezone-aware
        published_at = content.published_at
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        
        hours_elapsed = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
        
        if hours_elapsed < 1:
            hours_elapsed = 1  # Avoid division by zero
        
        metrics = content.raw_metrics or {}
        total_engagement = (
            metrics.get("likes", 0) +
            metrics.get("comments", 0) +
            metrics.get("reposts", 0) +
            metrics.get("bookmarks", 0)
        )
        
        # Engagement per hour
        velocity = total_engagement / hours_elapsed
        
        # Score based on velocity
        if velocity > 100:
            return 90.0
        elif velocity > 50:
            return 80.0
        elif velocity > 20:
            return 70.0
        elif velocity > 10:
            return 60.0
        elif velocity > 5:
            return 50.0
        else:
            return 40.0
    
    def _calculate_scarcity(self, content: Content) -> float:
        """Calculate topic/domain scarcity.
        
        Content in under-represented topics gets higher scores.
        """
        # Count recent content from same platform
        recent_count = self.db.query(func.count(Content.id)).filter(
            Content.platform == content.platform,
            Content.created_at > datetime.utcnow().replace(hour=0, minute=0, second=0),
        ).scalar()
        
        if recent_count == 0:
            return 70.0  # First content of the day
        
        # Calculate position in daily content (earlier = more scarce)
        daily_position = self.db.query(func.count(Content.id)).filter(
            Content.platform == content.platform,
            Content.created_at < content.created_at,
            Content.created_at > datetime.utcnow().replace(hour=0, minute=0, second=0),
        ).scalar()
        
        # Earlier content gets higher scarcity score
        scarcity_ratio = 1 - (daily_position / max(recent_count, 1))
        
        return 40 + scarcity_ratio * 40  # Range: 40-80
