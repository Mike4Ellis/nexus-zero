"""FastAPI application for Nexus Zero."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import date

from src.memory_db import memory_db

app = FastAPI(
    title="Nexus Zero API",
    description="智能信息聚合与筛选中心 API",
    version="0.1.0",
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class StatsResponse(BaseModel):
    totalContents: int
    todayContents: int
    pendingBriefs: int
    activeSources: int


class BriefResponse(BaseModel):
    id: int
    title: str
    date: str
    totalContents: int
    platforms: Dict[str, int]
    heatTopCount: int
    potentialCount: int


class ContentItem(BaseModel):
    id: int
    title: str
    platform: str
    published_at: str
    heat_score: float
    potential_score: float


# API Routes
@app.get("/")
async def root():
    return {"message": "Nexus Zero API", "version": "0.1.0"}


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get current statistics."""
    stats = memory_db.get_stats()
    return StatsResponse(
        totalContents=stats["total_contents"],
        todayContents=stats["today_contents"],
        pendingBriefs=stats["pending_briefs"],
        activeSources=stats["active_sources"],
    )


@app.get("/api/briefs/latest", response_model=BriefResponse)
async def get_latest_brief():
    """Get the latest daily brief."""
    brief = memory_db.get_latest_brief()
    if not brief:
        raise HTTPException(status_code=404, detail="No brief found")
    
    return BriefResponse(
        id=brief["id"],
        title=brief["title"],
        date=brief["date"],
        totalContents=brief["total_contents"],
        platforms=brief["platforms"],
        heatTopCount=brief["heat_top_count"],
        potentialCount=brief["potential_count"],
    )


@app.get("/api/briefs", response_model=List[BriefResponse])
async def get_briefs(limit: int = 10):
    """Get recent briefs."""
    briefs = memory_db._data["briefs"][-limit:]
    return [
        BriefResponse(
            id=b["id"],
            title=b["title"],
            date=b["date"],
            totalContents=b["total_contents"],
            platforms=b["platforms"],
            heatTopCount=b["heat_top_count"],
            potentialCount=b["potential_count"],
        )
        for b in reversed(briefs)
    ]


@app.get("/api/contents", response_model=List[ContentItem])
async def get_contents(limit: int = 100, platform: Optional[str] = None):
    """Get contents with optional filtering."""
    contents = memory_db.get_contents(limit=limit)
    
    if platform:
        contents = [c for c in contents if c["platform"] == platform]
    
    return [
        ContentItem(
            id=c["id"],
            title=c["title"],
            platform=c["platform"],
            published_at=c["published_at"],
            heat_score=c.get("heat_score", 0),
            potential_score=c.get("potential_score", 0),
        )
        for c in contents
    ]


@app.get("/api/sources")
async def get_sources():
    """Get all active sources."""
    return memory_db.get_sources()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
