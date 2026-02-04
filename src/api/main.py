"""FastAPI application for Nexus Zero."""

import time
from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.memory_db import memory_db

# Request timing middleware
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("🚀 Nexus Zero API starting up...")
    yield
    # Shutdown
    print("👋 Nexus Zero API shutting down...")


app = FastAPI(
    title="Nexus Zero API",
    description="智能信息聚合与筛选中心 API",
    version="0.1.0",
    lifespan=lifespan,
)

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.middleware("http")(add_process_time_header)


# Pydantic models with validation
class StatsResponse(BaseModel):
    totalContents: int = Field(..., ge=0)
    todayContents: int = Field(..., ge=0)
    pendingBriefs: int = Field(..., ge=0)
    activeSources: int = Field(..., ge=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "totalContents": 1234,
                "todayContents": 56,
                "pendingBriefs": 2,
                "activeSources": 4,
            }
        }


class BriefResponse(BaseModel):
    id: int
    title: str
    date: str
    totalContents: int = Field(..., ge=0)
    platforms: Dict[str, int]
    heatTopCount: int = Field(..., ge=0)
    potentialCount: int = Field(..., ge=0)
    summary: Optional[str] = None


class ContentItem(BaseModel):
    id: int
    title: str
    platform: str
    published_at: str
    heat_score: float = Field(..., ge=0, le=100)
    potential_score: float = Field(..., ge=0, le=100)


class SourceResponse(BaseModel):
    id: int
    name: str
    platform: str
    is_active: bool


class ErrorResponse(BaseModel):
    detail: str
    timestamp: str


# Custom exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "timestamp": datetime.now().isoformat(),
        },
    )


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0",
    }


@app.get("/", tags=["System"])
async def root():
    """API root endpoint."""
    return {
        "message": "Nexus Zero API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/api/stats", response_model=StatsResponse, tags=["Statistics"])
async def get_stats():
    """
    Get current statistics.
    
    Returns aggregated statistics about contents, briefs, and sources.
    """
    try:
        stats = memory_db.get_stats()
        return StatsResponse(
            totalContents=stats["total_contents"],
            todayContents=stats["today_contents"],
            pendingBriefs=stats["pending_briefs"],
            activeSources=stats["active_sources"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.get("/api/briefs/latest", response_model=BriefResponse, tags=["Briefs"])
async def get_latest_brief():
    """
    Get the latest daily brief.
    
    Returns the most recent briefing with content summary and platform distribution.
    """
    try:
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
            summary=brief.get("summary"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get latest brief: {str(e)}")


@app.get("/api/briefs", response_model=List[BriefResponse], tags=["Briefs"])
async def get_briefs(
    limit: int = Query(10, ge=1, le=100, description="Number of briefs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    Get recent briefs with pagination.
    
    - **limit**: Number of briefs to return (1-100)
    - **offset**: Offset for pagination
    """
    try:
        all_briefs = memory_db._data["briefs"]
        briefs = all_briefs[-(offset + limit):-offset or None]
        
        return [
            BriefResponse(
                id=b["id"],
                title=b["title"],
                date=b["date"],
                totalContents=b["total_contents"],
                platforms=b["platforms"],
                heatTopCount=b["heat_top_count"],
                potentialCount=b["potential_count"],
                summary=b.get("summary"),
            )
            for b in reversed(briefs)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get briefs: {str(e)}")


@app.get("/api/contents", response_model=List[ContentItem], tags=["Contents"])
async def get_contents(
    limit: int = Query(100, ge=1, le=1000, description="Number of contents to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    platform: Optional[str] = Query(None, description="Filter by platform (x, reddit, rss, xiaohongshu)"),
    min_heat_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum heat score filter"),
    min_potential_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum potential score filter"),
):
    """
    Get contents with filtering and pagination.
    
    - **limit**: Number of contents to return (1-1000)
    - **offset**: Offset for pagination
    - **platform**: Filter by platform
    - **min_heat_score**: Minimum heat score filter
    - **min_potential_score**: Minimum potential score filter
    """
    try:
        contents = memory_db.get_contents(limit=limit + offset)
        contents = contents[offset:]
        
        if platform:
            contents = [c for c in contents if c["platform"] == platform]
        
        if min_heat_score is not None:
            contents = [c for c in contents if c.get("heat_score", 0) >= min_heat_score]
        
        if min_potential_score is not None:
            contents = [c for c in contents if c.get("potential_score", 0) >= min_potential_score]
        
        return [
            ContentItem(
                id=c["id"],
                title=c["title"],
                platform=c["platform"],
                published_at=c["published_at"],
                heat_score=c.get("heat_score", 0),
                potential_score=c.get("potential_score", 0),
            )
            for c in contents[:limit]
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get contents: {str(e)}")


@app.get("/api/sources", response_model=List[SourceResponse], tags=["Sources"])
async def get_sources(
    active_only: bool = Query(True, description="Return only active sources"),
):
    """
    Get all sources.
    
    - **active_only**: If true, return only active sources
    """
    try:
        sources = memory_db.get_sources()
        if active_only:
            sources = [s for s in sources if s.get("is_active", True)]
        
        return [
            SourceResponse(
                id=s["id"],
                name=s["name"],
                platform=s["platform"],
                is_active=s.get("is_active", True),
            )
            for s in sources
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sources: {str(e)}")


@app.get("/api/platforms", tags=["Statistics"])
async def get_platforms():
    """Get available platforms and their content counts."""
    try:
        contents = memory_db.get_contents(limit=10000)
        platforms = {}
        
        for content in contents:
            platform = content["platform"]
            platforms[platform] = platforms.get(platform, 0) + 1
        
        return {
            "platforms": [
                {"name": name, "count": count}
                for name, count in sorted(platforms.items(), key=lambda x: x[1], reverse=True)
            ],
            "total": len(contents),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get platforms: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
