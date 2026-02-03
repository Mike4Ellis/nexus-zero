"""X (Twitter) content fetcher using Tweepy."""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.fetcher.base import BaseFetcher, FetchResult
from src.models.source import Source


class XFetcher(BaseFetcher):
    """Fetcher for X (formerly Twitter) content."""
    
    def __init__(self, source: Source, db: Session):
        super().__init__(source, db)
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Tweepy client with API credentials."""
        try:
            import tweepy
        except ImportError:
            raise ImportError("tweepy is required for X fetching. Install with: pip install tweepy")
        
        # Get credentials from source config or environment
        bearer_token = (
            self.source.config.get("bearer_token") 
            or os.getenv("X_BEARER_TOKEN")
        )
        
        if not bearer_token:
            raise ValueError("X bearer token not configured")
        
        self.client = tweepy.Client(
            bearer_token=bearer_token,
            wait_on_rate_limit=True,
        )
    
    def get_platform(self) -> str:
        return "x"
    
    def fetch(self, since: Optional[datetime] = None) -> FetchResult:
        """Fetch tweets based on source configuration.
        
        Source config options:
        - query: Search query (required for search mode)
        - user_id: User ID to fetch timeline (alternative to query)
        - max_results: Max tweets per fetch (default: 100)
        - tweet_fields: Fields to include (default: all)
        """
        if not self.client:
            return FetchResult(items=[], error="X client not initialized")
        
        try:
            config = self.source.config or {}
            max_results = min(config.get("max_results", 100), 100)
            
            # Determine fetch mode
            if "user_id" in config:
                # Fetch user timeline
                tweets = self._fetch_user_timeline(
                    user_id=config["user_id"],
                    max_results=max_results,
                    since=since,
                )
            elif "query" in config:
                # Search tweets
                tweets = self._fetch_search(
                    query=config["query"],
                    max_results=max_results,
                    since=since,
                )
            else:
                return FetchResult(
                    items=[],
                    error="Source config must contain 'user_id' or 'query'",
                )
            
            return FetchResult(
                items=tweets,
                total_fetched=len(tweets),
            )
            
        except Exception as e:
            return FetchResult(items=[], error=f"X fetch failed: {str(e)}")
    
    def _fetch_user_timeline(
        self,
        user_id: str,
        max_results: int = 100,
        since: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch tweets from a user's timeline."""
        import tweepy
        
        # Build query parameters
        params = {
            "max_results": max_results,
            "tweet_fields": [
                "created_at",
                "public_metrics",
                "entities",
                "attachments",
                "author_id",
                "context_annotations",
            ],
            "exclude": ["retweets", "replies"],
        }
        
        # Add time-based pagination if since is provided
        if since:
            # Convert to ISO format for API
            params["start_time"] = since.isoformat()
        
        # Fetch tweets
        response = self.client.get_users_tweets(user_id, **params)
        
        if not response.data:
            return []
        
        # Convert to raw data format
        tweets = []
        for tweet in response.data:
            tweet_dict = {
                "id": tweet.id,
                "text": tweet.text,
                "created_at": tweet.created_at,
                "author_id": tweet.author_id,
                "public_metrics": tweet.public_metrics or {},
                "entities": tweet.entities or {},
            }
            tweets.append(tweet_dict)
        
        return tweets
    
    def _fetch_search(
        self,
        query: str,
        max_results: int = 100,
        since: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Search for tweets matching query."""
        import tweepy
        
        # Build query parameters
        params = {
            "query": query,
            "max_results": max_results,
            "tweet_fields": [
                "created_at",
                "public_metrics",
                "entities",
                "attachments",
                "author_id",
                "context_annotations",
            ],
        }
        
        # Add time filter if since is provided
        if since:
            params["start_time"] = since.isoformat()
        
        # Fetch tweets
        response = self.client.search_recent_tweets(**params)
        
        if not response.data:
            return []
        
        # Convert to raw data format
        tweets = []
        for tweet in response.data:
            tweet_dict = {
                "id": tweet.id,
                "text": tweet.text,
                "created_at": tweet.created_at,
                "author_id": tweet.author_id,
                "public_metrics": tweet.public_metrics or {},
                "entities": tweet.entities or {},
            }
            tweets.append(tweet_dict)
        
        return tweets
    
    def parse_item(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse X tweet data into standardized format."""
        try:
            metrics = raw_data.get("public_metrics", {})
            
            return {
                "external_id": str(raw_data["id"]),
                "title": None,  # X tweets don't have titles
                "content": raw_data["text"],
                "author_id": raw_data.get("author_id"),
                "url": f"https://x.com/i/status/{raw_data['id']}",
                "published_at": raw_data["created_at"],
                "raw_metrics": {
                    "views": metrics.get("impression_count", 0),
                    "likes": metrics.get("like_count", 0),
                    "reposts": metrics.get("retweet_count", 0),
                    "replies": metrics.get("reply_count", 0),
                    "bookmarks": metrics.get("bookmark_count", 0),
                    "quotes": metrics.get("quote_count", 0),
                },
                "media_urls": self._extract_media_urls(raw_data),
            }
        except (KeyError, ValueError) as e:
            # Log parsing error but don't fail entire batch
            print(f"Failed to parse tweet {raw_data.get('id')}: {e}")
            return None
    
    def _extract_media_urls(self, raw_data: Dict[str, Any]) -> List[str]:
        """Extract media URLs from tweet entities."""
        urls = []
        entities = raw_data.get("entities", {})
        
        # Extract from media entities
        media = entities.get("media", [])
        for item in media:
            if "url" in item:
                urls.append(item["url"])
            elif "media_url_https" in item:
                urls.append(item["media_url_https"])
        
        # Extract from URLs entities
        urls_data = entities.get("urls", [])
        for item in urls_data:
            if "expanded_url" in item:
                urls.append(item["expanded_url"])
        
        return urls


def create_x_source(
    db: Session,
    name: str,
    query: Optional[str] = None,
    user_id: Optional[str] = None,
    max_results: int = 100,
) -> Source:
    """Helper to create an X source configuration."""
    if not query and not user_id:
        raise ValueError("Either query or user_id must be provided")
    
    config = {"max_results": max_results}
    if query:
        config["query"] = query
    if user_id:
        config["user_id"] = user_id
    
    source = Source(
        name=name,
        platform="x",
        config=config,
        is_active=True,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source
