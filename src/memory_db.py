"""In-memory database for development and testing."""

from datetime import datetime, date
from typing import Dict, List, Optional, Any
import json

class InMemoryDB:
    """Simple in-memory database with JSON serialization."""
    
    def __init__(self):
        self._data = {
            "contents": [],
            "sources": [],
            "briefs": [],
            "stats": {
                "total_contents": 1234,
                "today_contents": 56,
                "pending_briefs": 2,
                "active_sources": 4,
            }
        }
        self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        """Initialize with realistic mock data."""
        # Initialize sources
        self._data["sources"] = [
            {"id": 1, "name": "X-Tech", "platform": "x", "is_active": True},
            {"id": 2, "name": "Reddit-AI", "platform": "reddit", "is_active": True},
            {"id": 3, "name": "RSS-News", "platform": "rss", "is_active": True},
            {"id": 4, "name": "小红书", "platform": "xiaohongshu", "is_active": True},
        ]
        
        # Initialize contents
        self._data["contents"] = [
            {
                "id": i,
                "title": f"Content {i}",
                "platform": ["x", "reddit", "rss"][i % 3],
                "published_at": datetime.now().isoformat(),
                "heat_score": 50 + (i * 5) % 50,
                "potential_score": 40 + (i * 7) % 40,
            }
            for i in range(1, 43)
        ]
        
        # Initialize latest brief
        self._data["briefs"] = [
            {
                "id": 1,
                "title": "Nexus Zero 每日简报 - 2026-02-04",
                "date": date.today().isoformat(),
                "total_contents": 42,
                "platforms": {"x": 15, "reddit": 12, "rss": 15},
                "heat_top_count": 10,
                "potential_count": 5,
                "summary": "今日共收录42条内容，其中热门精选10条，潜力发现5条。",
            }
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        return self._data["stats"].copy()
    
    def update_stats(self, stats: Dict[str, Any]):
        """Update statistics."""
        self._data["stats"].update(stats)
    
    def get_latest_brief(self) -> Optional[Dict[str, Any]]:
        """Get the latest brief."""
        if not self._data["briefs"]:
            return None
        return self._data["briefs"][-1].copy()
    
    def add_brief(self, brief: Dict[str, Any]):
        """Add a new brief."""
        brief["id"] = len(self._data["briefs"]) + 1
        self._data["briefs"].append(brief)
    
    def get_contents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get contents with limit."""
        return self._data["contents"][:limit]
    
    def add_content(self, content: Dict[str, Any]):
        """Add new content."""
        content["id"] = len(self._data["contents"]) + 1
        self._data["contents"].append(content)
        self._data["stats"]["total_contents"] += 1
        self._data["stats"]["today_contents"] += 1
    
    def get_sources(self) -> List[Dict[str, Any]]:
        """Get all sources."""
        return self._data["sources"].copy()
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self._data, default=str, indent=2)
    
    def from_json(self, json_str: str):
        """Load from JSON."""
        self._data = json.loads(json_str)

# Global instance
memory_db = InMemoryDB()
