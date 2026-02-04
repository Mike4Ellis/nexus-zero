"""In-memory database for development and testing."""

import json
import threading
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional


class InMemoryDB:
    """Thread-safe in-memory database with JSON serialization."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._data = {
            "contents": [],
            "sources": [],
            "briefs": [],
            "stats": {
                "total_contents": 0,
                "today_contents": 0,
                "pending_briefs": 0,
                "active_sources": 0,
            }
        }
        self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        """Initialize with realistic mock data."""
        with self._lock:
            # Initialize sources
            self._data["sources"] = [
                {"id": 1, "name": "X-Tech", "platform": "x", "is_active": True, "config": {"keywords": ["AI", "tech"]}},
                {"id": 2, "name": "Reddit-AI", "platform": "reddit", "is_active": True, "config": {"subreddits": ["r/MachineLearning", "r/artificial"]}},
                {"id": 3, "name": "RSS-News", "platform": "rss", "is_active": True, "config": {"feeds": ["https://example.com/feed.xml"]}},
                {"id": 4, "name": "小红书", "platform": "xiaohongshu", "is_active": True, "config": {"tags": ["科技", "AI"]}},
            ]
            
            # Initialize contents with varied scores
            platforms = ["x", "reddit", "rss", "xiaohongshu"]
            contents = []
            base_time = datetime.now() - timedelta(days=7)
            
            for i in range(1, 101):
                platform = platforms[i % len(platforms)]
                heat_score = 30 + (i * 3) % 70  # 30-100 range
                potential_score = 20 + (i * 5) % 80  # 20-100 range
                
                contents.append({
                    "id": i,
                    "title": f"Content {i}: {'热门' if heat_score > 70 else '普通'}内容示例",
                    "platform": platform,
                    "author": f"user_{i}",
                    "url": f"https://example.com/content/{i}",
                    "published_at": (base_time + timedelta(hours=i)).isoformat(),
                    "heat_score": round(heat_score, 2),
                    "potential_score": round(potential_score, 2),
                    "raw_metrics": {
                        "views": 1000 + i * 100,
                        "likes": 50 + i * 10,
                        "comments": 10 + i * 2,
                    },
                    "is_processed": True,
                    "is_briefed": heat_score > 60,
                })
            
            self._data["contents"] = contents
            
            # Calculate initial stats
            today = date.today().isoformat()
            today_contents = sum(
                1 for c in contents
                if c["published_at"].startswith(today)
            )
            
            self._data["stats"] = {
                "total_contents": len(contents),
                "today_contents": today_contents,
                "pending_briefs": 2,
                "active_sources": len([s for s in self._data["sources"] if s["is_active"]]),
            }
            
            # Initialize briefs
            self._data["briefs"] = [
                {
                    "id": 1,
                    "title": f"Nexus Zero 每日简报 - {date.today().isoformat()}",
                    "date": date.today().isoformat(),
                    "total_contents": 42,
                    "platforms": {"x": 15, "reddit": 12, "rss": 10, "xiaohongshu": 5},
                    "heat_top_count": 10,
                    "potential_count": 8,
                    "summary": "今日共收录42条内容，其中热门精选10条，潜力发现8条。主要关注AI技术动态和产品发布。",
                    "featured_ids": [95, 88, 76, 65, 54, 43, 32, 21, 15, 8],
                    "created_at": datetime.now().isoformat(),
                }
            ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        with self._lock:
            return self._data["stats"].copy()
    
    def update_stats(self, stats: Dict[str, Any]):
        """Update statistics."""
        with self._lock:
            self._data["stats"].update(stats)
    
    def get_latest_brief(self) -> Optional[Dict[str, Any]]:
        """Get the latest brief."""
        with self._lock:
            if not self._data["briefs"]:
                return None
            return self._data["briefs"][-1].copy()
    
    def get_brief_by_id(self, brief_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific brief by ID."""
        with self._lock:
            for brief in self._data["briefs"]:
                if brief["id"] == brief_id:
                    return brief.copy()
            return None
    
    def add_brief(self, brief: Dict[str, Any]) -> int:
        """Add a new brief and return its ID."""
        with self._lock:
            brief_id = len(self._data["briefs"]) + 1
            brief["id"] = brief_id
            brief["created_at"] = datetime.now().isoformat()
            self._data["briefs"].append(brief)
            return brief_id
    
    def get_contents(
        self,
        limit: int = 100,
        offset: int = 0,
        platform: Optional[str] = None,
        min_heat: Optional[float] = None,
        min_potential: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Get contents with filtering."""
        with self._lock:
            contents = self._data["contents"][:]
            
            if platform:
                contents = [c for c in contents if c["platform"] == platform]
            
            if min_heat is not None:
                contents = [c for c in contents if c.get("heat_score", 0) >= min_heat]
            
            if min_potential is not None:
                contents = [c for c in contents if c.get("potential_score", 0) >= min_potential]
            
            # Sort by published_at desc
            contents.sort(key=lambda x: x["published_at"], reverse=True)
            
            return contents[offset:offset + limit]
    
    def get_content_by_id(self, content_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific content by ID."""
        with self._lock:
            for content in self._data["contents"]:
                if content["id"] == content_id:
                    return content.copy()
            return None
    
    def add_content(self, content: Dict[str, Any]) -> int:
        """Add new content and return its ID."""
        with self._lock:
            content_id = len(self._data["contents"]) + 1
            content["id"] = content_id
            content["published_at"] = datetime.now().isoformat()
            self._data["contents"].append(content)
            
            # Update stats
            self._data["stats"]["total_contents"] += 1
            self._data["stats"]["today_contents"] += 1
            
            return content_id
    
    def get_sources(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """Get all sources."""
        with self._lock:
            sources = self._data["sources"][:]
            if active_only:
                sources = [s for s in sources if s.get("is_active", True)]
            return [s.copy() for s in sources]
    
    def get_source_by_id(self, source_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific source by ID."""
        with self._lock:
            for source in self._data["sources"]:
                if source["id"] == source_id:
                    return source.copy()
            return None
    
    def update_source(self, source_id: int, updates: Dict[str, Any]) -> bool:
        """Update a source."""
        with self._lock:
            for source in self._data["sources"]:
                if source["id"] == source_id:
                    source.update(updates)
                    source["updated_at"] = datetime.now().isoformat()
                    return True
            return False
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        with self._lock:
            return json.dumps(self._data, default=str, indent=2)
    
    def from_json(self, json_str: str):
        """Load from JSON."""
        with self._lock:
            self._data = json.loads(json_str)
    
    def export_to_dict(self) -> Dict[str, Any]:
        """Export all data as dictionary."""
        with self._lock:
            return {
                "stats": self._data["stats"].copy(),
                "sources_count": len(self._data["sources"]),
                "contents_count": len(self._data["contents"]),
                "briefs_count": len(self._data["briefs"]),
                "latest_brief": self._data["briefs"][-1].copy() if self._data["briefs"] else None,
            }


# Global instance
memory_db = InMemoryDB()
