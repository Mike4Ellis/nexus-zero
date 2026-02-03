"""Heat score calculation based on engagement and time decay."""

from datetime import datetime, timezone
from typing import Dict

from src.models.content import Content
from src.scorer.base import BaseScorer, ScoreResult


class HeatScorer(BaseScorer):
    """Calculates heat score based on engagement metrics and time decay.
    
    Heat Score Formula:
    - Base engagement score from raw metrics
    - Time decay factor (newer content scores higher)
    - Platform-specific normalization
    """
    
    # Weight configuration for different engagement types
    METRIC_WEIGHTS = {
        "views": 0.1,
        "likes": 1.0,
        "reposts": 2.0,
        "comments": 3.0,
        "bookmarks": 2.5,
    }
    
    # Time decay parameters
    HALF_LIFE_HOURS = 24  # Score halves after 24 hours
    MIN_DECAY = 0.1  # Minimum decay factor (10%)
    
    def get_score_type(self) -> str:
        return "heat"
    
    def calculate(self, content: Content) -> ScoreResult:
        """Calculate heat score for content."""
        try:
            # Get raw metrics
            metrics = content.raw_metrics or {}
            
            # Calculate base engagement score
            engagement_score = self._calculate_engagement(metrics)
            
            # Calculate time decay factor
            decay_factor = self._calculate_time_decay(content.published_at)
            
            # Calculate platform normalization
            platform_factor = self._get_platform_factor(content.platform)
            
            # Final heat score
            heat_score = engagement_score * decay_factor * platform_factor
            
            # Normalize to 0-100 range
            normalized_score = min(100.0, max(0.0, heat_score))
            
            return ScoreResult(
                score=round(normalized_score, 2),
                factors={
                    "engagement_score": round(engagement_score, 2),
                    "decay_factor": round(decay_factor, 4),
                    "platform_factor": round(platform_factor, 2),
                    "raw_metrics": metrics,
                },
            )
            
        except Exception as e:
            return ScoreResult(
                score=0.0,
                factors={"error": str(e)},
                success=False,
                error=str(e),
            )
    
    def _calculate_engagement(self, metrics: Dict) -> float:
        """Calculate weighted engagement score from raw metrics."""
        score = 0.0
        
        for metric, weight in self.METRIC_WEIGHTS.items():
            value = metrics.get(metric, 0)
            # Normalize large numbers (log scale for views)
            if metric == "views" and value > 0:
                normalized_value = 10 * (1 + value / 1000) ** 0.5
            else:
                normalized_value = value
            
            score += normalized_value * weight
        
        # Apply logarithmic scaling to prevent extreme values
        if score > 0:
            score = 10 * (1 + score) ** 0.5
        
        return score
    
    def _calculate_time_decay(self, published_at: datetime) -> float:
        """Calculate time decay factor.
        
        Uses exponential decay: decay = max(MIN_DECAY, 0.5^(hours/HALF_LIFE))
        """
        if not published_at:
            return 1.0
        
        # Ensure published_at is timezone-aware
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        hours_elapsed = (now - published_at).total_seconds() / 3600
        
        # Exponential decay
        import math
        decay = math.pow(0.5, hours_elapsed / self.HALF_LIFE_HOURS)
        
        # Apply minimum decay floor
        return max(self.MIN_DECAY, decay)
    
    def _get_platform_factor(self, platform: str) -> float:
        """Get platform-specific normalization factor.
        
        Different platforms have different engagement scales.
        This normalizes them to a comparable range.
        """
        platform_factors = {
            "x": 1.0,  # Baseline
            "reddit": 0.8,  # Reddit scores tend to be lower
            "rss": 0.5,  # RSS has no native engagement metrics
            "xiaohongshu": 1.2,  # Higher engagement rates
        }
        
        return platform_factors.get(platform, 1.0)
