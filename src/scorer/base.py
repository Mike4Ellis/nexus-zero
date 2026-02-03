"""Base scorer class for content quality scoring."""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.models.content import Content
from src.models.score import Score


class ScoreResult:
    """Result of a scoring operation."""
    
    def __init__(
        self,
        score: float,
        factors: Dict[str, float],
        success: bool = True,
        error: Optional[str] = None,
    ):
        self.score = score
        self.factors = factors
        self.success = success
        self.error = error


class BaseScorer(ABC):
    """Abstract base class for content scorers."""
    
    def __init__(self, db: Session):
        self.db = db
        self.score_type = self.get_score_type()
        self.algorithm_version = "1.0"
    
    @abstractmethod
    def get_score_type(self) -> str:
        """Return the score type identifier (e.g., 'heat', 'potential')."""
        raise NotImplementedError
    
    @abstractmethod
    def calculate(self, content: Content) -> ScoreResult:
        """Calculate score for a single content item.
        
        Returns:
            ScoreResult with score (0-100) and factor breakdown
        """
        raise NotImplementedError
    
    def score_content(self, content: Content) -> Optional[Score]:
        """Calculate and save score for content."""
        result = self.calculate(content)
        
        if not result.success:
            return None
        
        # Check if score already exists
        existing = self.db.query(Score).filter(
            Score.content_id == content.id,
            Score.score_type == self.score_type,
        ).first()
        
        if existing:
            # Update existing score
            existing.score = result.score
            existing.factors = result.factors
            existing.algorithm_version = self.algorithm_version
            existing.calculated_at = datetime.utcnow()
            score = existing
        else:
            # Create new score
            score = Score(
                content_id=content.id,
                score_type=self.score_type,
                score=result.score,
                factors=result.factors,
                algorithm_version=self.algorithm_version,
            )
            self.db.add(score)
        
        # Mark content as processed
        content.is_processed = True
        self.db.commit()
        
        return score
    
    def score_batch(self, contents: List[Content]) -> int:
        """Score multiple content items.
        
        Returns:
            Number of items scored
        """
        scored_count = 0
        
        for content in contents:
            try:
                score = self.score_content(content)
                if score:
                    scored_count += 1
            except Exception as e:
                print(f"Failed to score content {content.id}: {e}")
                continue
        
        return scored_count
    
    def score_unprocessed(self, limit: Optional[int] = None) -> int:
        """Score all unprocessed content.
        
        Returns:
            Number of items scored
        """
        query = self.db.query(Content).filter(Content.is_processed == False)
        
        if limit:
            query = query.limit(limit)
        
        contents = query.all()
        return self.score_batch(contents)
