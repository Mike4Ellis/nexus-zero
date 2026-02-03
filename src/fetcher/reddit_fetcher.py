"""Reddit content fetcher using PRAW."""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.fetcher.base import BaseFetcher, FetchResult
from src.models.source import Source


class RedditFetcher(BaseFetcher):
    """Fetcher for Reddit content."""
    
    def __init__(self, source: Source, db: Session):
        super().__init__(source, db)
        self.reddit = None
        self._init_client()
    
    def _init_client(self):
        """Initialize PRAW Reddit client."""
        try:
            import praw
        except ImportError:
            raise ImportError("praw is required for Reddit fetching. Install with: pip install praw")
        
        # Get credentials from source config or environment
        config = self.source.config or {}
        
        client_id = config.get("client_id") or os.getenv("REDDIT_CLIENT_ID")
        client_secret = config.get("client_secret") or os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = config.get("user_agent") or os.getenv(
            "REDDIT_USER_AGENT", 
            "InfoFlow/0.1.0"
        )
        
        if not client_id or not client_secret:
            raise ValueError("Reddit client credentials not configured")
        
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
    
    def get_platform(self) -> str:
        return "reddit"
    
    def fetch(self, since: Optional[datetime] = None) -> FetchResult:
        """Fetch Reddit posts based on source configuration.
        
        Source config options:
        - subreddit: Subreddit name (required)
        - sort: Sort method - 'hot', 'new', 'top', 'rising' (default: 'hot')
        - limit: Max posts to fetch (default: 100)
        - time_filter: For 'top' sort - 'all', 'day', 'hour', 'month', 'week', 'year'
        """
        if not self.reddit:
            return FetchResult(items=[], error="Reddit client not initialized")
        
        try:
            config = self.source.config or {}
            subreddit_name = config.get("subreddit")
            
            if not subreddit_name:
                return FetchResult(
                    items=[],
                    error="Source config must contain 'subreddit'",
                )
            
            sort_method = config.get("sort", "hot")
            limit = min(config.get("limit", 100), 100)
            time_filter = config.get("time_filter", "day")
            
            # Get subreddit
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Fetch posts based on sort method
            if sort_method == "hot":
                posts = subreddit.hot(limit=limit)
            elif sort_method == "new":
                posts = subreddit.new(limit=limit)
            elif sort_method == "top":
                posts = subreddit.top(time_filter=time_filter, limit=limit)
            elif sort_method == "rising":
                posts = subreddit.rising(limit=limit)
            else:
                return FetchResult(
                    items=[],
                    error=f"Invalid sort method: {sort_method}",
                )
            
            # Convert to list and filter by time if needed
            posts_data = []
            for post in posts:
                post_data = {
                    "id": post.id,
                    "title": post.title,
                    "selftext": post.selftext,
                    "author": str(post.author) if post.author else None,
                    "created_utc": post.created_utc,
                    "score": post.score,
                    "upvote_ratio": post.upvote_ratio,
                    "num_comments": post.num_comments,
                    "url": post.url,
                    "permalink": post.permalink,
                    "is_self": post.is_self,
                    "subreddit": post.subreddit.display_name,
                }
                
                # Filter by time if since is provided
                if since:
                    post_time = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
                    if post_time < since:
                        continue
                
                posts_data.append(post_data)
            
            return FetchResult(
                items=posts_data,
                total_fetched=len(posts_data),
            )
            
        except Exception as e:
            return FetchResult(items=[], error=f"Reddit fetch failed: {str(e)}")
    
    def parse_item(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Reddit post data into standardized format."""
        try:
            # Build content text
            title = raw_data.get("title", "")
            body = raw_data.get("selftext", "")
            
            if body:
                content = f"{title}\n\n{body}"
            else:
                content = title
            
            # Convert Unix timestamp to datetime
            created_utc = raw_data.get("created_utc", 0)
            published_at = datetime.fromtimestamp(created_utc, tz=timezone.utc)
            
            # Calculate engagement metrics
            score = raw_data.get("score", 0)
            upvote_ratio = raw_data.get("upvote_ratio", 0.5)
            num_comments = raw_data.get("num_comments", 0)
            
            # Estimate views (Reddit doesn't provide this directly)
            # Rough estimate: score / upvote_ratio gives approximate total votes
            estimated_votes = int(score / upvote_ratio) if upvote_ratio > 0 else score
            estimated_views = estimated_votes * 10  # Rough ratio
            
            return {
                "external_id": raw_data["id"],
                "title": title,
                "content": content,
                "author": raw_data.get("author"),
                "url": f"https://reddit.com{raw_data['permalink']}",
                "published_at": published_at,
                "raw_metrics": {
                    "views": estimated_views,
                    "likes": score,  # Reddit score (upvotes - downvotes)
                    "upvote_ratio": upvote_ratio,
                    "comments": num_comments,
                    "reposts": 0,  # Reddit doesn't track reposts directly
                    "bookmarks": 0,  # Not available via API
                },
                "media_urls": [raw_data["url"]] if not raw_data.get("is_self") else [],
            }
        except (KeyError, ValueError) as e:
            print(f"Failed to parse Reddit post {raw_data.get('id')}: {e}")
            return None


def create_reddit_source(
    db: Session,
    name: str,
    subreddit: str,
    sort: str = "hot",
    limit: int = 100,
    time_filter: str = "day",
) -> Source:
    """Helper to create a Reddit source configuration."""
    config = {
        "subreddit": subreddit,
        "sort": sort,
        "limit": limit,
        "time_filter": time_filter,
    }
    
    source = Source(
        name=name,
        platform="reddit",
        config=config,
        is_active=True,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source
