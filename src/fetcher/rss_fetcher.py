"""RSS/Atom feed fetcher using feedparser."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from src.fetcher.base import BaseFetcher, FetchResult
from src.models.source import Source


class RSSFetcher(BaseFetcher):
    """Fetcher for RSS/Atom feeds."""
    
    def __init__(self, source: Source, db: Session):
        super().__init__(source, db)
        self.client = httpx.Client(timeout=30.0, follow_redirects=True)
    
    def get_platform(self) -> str:
        return "rss"
    
    def fetch(self, since: Optional[datetime] = None) -> FetchResult:
        """Fetch RSS feed based on source configuration.
        
        Source config options:
        - url: RSS feed URL (required)
        - max_entries: Max entries to fetch (default: 50)
        """
        try:
            import feedparser
        except ImportError:
            return FetchResult(
                items=[],
                error="feedparser is required. Install with: pip install feedparser",
            )
        
        config = self.source.config or {}
        feed_url = config.get("url")
        
        if not feed_url:
            return FetchResult(
                items=[],
                error="Source config must contain 'url'",
            )
        
        max_entries = min(config.get("max_entries", 50), 100)
        
        try:
            # Fetch feed content
            response = self.client.get(feed_url)
            response.raise_for_status()
            
            # Parse feed
            feed = feedparser.parse(response.content)
            
            if feed.bozo and feed.bozo_exception:
                # Feed has parsing issues but may still be usable
                print(f"Warning: Feed parsing issue: {feed.bozo_exception}")
            
            entries = []
            for entry in feed.entries[:max_entries]:
                entry_data = self._parse_entry(entry)
                if entry_data:
                    # Filter by time if since is provided
                    if since and entry_data.get("published_at"):
                        if entry_data["published_at"] < since:
                            continue
                    entries.append(entry_data)
            
            return FetchResult(
                items=entries,
                total_fetched=len(entries),
            )
            
        except httpx.HTTPError as e:
            return FetchResult(items=[], error=f"HTTP error fetching RSS: {str(e)}")
        except Exception as e:
            return FetchResult(items=[], error=f"RSS fetch failed: {str(e)}")
    
    def _parse_entry(self, entry: Any) -> Optional[Dict[str, Any]]:
        """Parse a feed entry into standardized format."""
        try:
            # Extract basic fields
            entry_id = entry.get("id") or entry.get("guid") or entry.get("link")
            if not entry_id:
                return None
            
            title = entry.get("title", "")
            
            # Get content (prefer content over summary)
            content = ""
            if "content" in entry:
                # Atom format
                content = entry.content[0].value if entry.content else ""
            elif "summary" in entry:
                content = entry.summary
            elif "description" in entry:
                content = entry.description
            
            # Clean HTML if present (simple approach)
            content = self._clean_html(content)
            
            # Parse published date
            published_at = None
            if "published_parsed" in entry:
                published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif "updated_parsed" in entry:
                published_at = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            
            # Extract author
            author = None
            if "author" in entry:
                author = entry.author
            elif "author_detail" in entry and entry.author_detail:
                author = entry.author_detail.get("name")
            
            # Extract media URLs
            media_urls = []
            if "media_content" in entry:
                for media in entry.media_content:
                    if "url" in media:
                        media_urls.append(media["url"])
            if "links" in entry:
                for link in entry.links:
                    if link.get("type", "").startswith("image/"):
                        media_urls.append(link["href"])
            
            # RSS doesn't provide engagement metrics
            # We'll set them to 0 and they can be updated later if available
            return {
                "external_id": entry_id,
                "title": title,
                "content": content or title,  # Fallback to title if no content
                "author": author,
                "url": entry.get("link"),
                "published_at": published_at or datetime.now(timezone.utc),
                "raw_metrics": {
                    "views": 0,
                    "likes": 0,
                    "reposts": 0,
                    "comments": 0,
                    "bookmarks": 0,
                },
                "media_urls": media_urls,
            }
            
        except Exception as e:
            print(f"Failed to parse RSS entry: {e}")
            return None
    
    def _clean_html(self, html: str) -> str:
        """Simple HTML cleaning."""
        try:
            from html.parser import HTMLParser
            
            class MLStripper(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.reset()
                    self.fed = []
                
                def handle_data(self, d):
                    self.fed.append(d)
                
                def get_data(self):
                    return "".join(self.fed)
            
            s = MLStripper()
            s.feed(html)
            return s.get_data().strip()
        except:
            # If parsing fails, return original
            return html
    
    def parse_item(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse RSS entry data (already parsed in fetch)."""
        # RSS entries are already parsed in _parse_entry
        return raw_data


def create_rss_source(
    db: Session,
    name: str,
    url: str,
    max_entries: int = 50,
) -> Source:
    """Helper to create an RSS source configuration."""
    config = {
        "url": url,
        "max_entries": max_entries,
    }
    
    source = Source(
        name=name,
        platform="rss",
        config=config,
        is_active=True,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source
