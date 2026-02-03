"""Task scheduler using APScheduler for Nexus Zero.

This module provides scheduled task execution for:
- Content fetching (every 4 hours)
- Score calculation (every 6 hours)
- Brief generation (daily at 8:00)
- Brief sending (daily at 8:30)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from src.config import get_settings
from src.database import SessionLocal
from src.fetcher.base import BaseFetcher
from src.fetcher.x_fetcher import XFetcher
from src.fetcher.reddit_fetcher import RedditFetcher
from src.fetcher.rss_fetcher import RSSFetcher
from src.scorer.heat_scorer import HeatScorer
from src.scorer.potential_scorer import PotentialScorer
from src.brief.generator import BriefGenerator
from src.brief.publisher import BriefPublisher
from src.models.source import Source

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Manages scheduled tasks for Nexus Zero."""
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.settings = get_settings()
        self._running = False
    
    def _get_db(self) -> Session:
        """Get database session."""
        return SessionLocal()
    
    def _job_listener(self, event):
        """Listen for job events."""
        if event.exception:
            logger.error(f"Job {event.job_id} crashed: {event.exception}")
        else:
            logger.info(f"Job {event.job_id} executed successfully")
    
    async def fetch_all_content(self):
        """Fetch content from all enabled sources."""
        logger.info("Starting scheduled content fetch")
        db = self._get_db()
        
        try:
            # Get all active sources
            sources = db.query(Source).filter(Source.is_active == True).all()
            
            for source in sources:
                try:
                    if source.platform == "x" and self.settings.enable_x_fetcher:
                        fetcher = XFetcher(source, db)
                        await asyncio.to_thread(fetcher.run)
                    elif source.platform == "reddit" and self.settings.enable_reddit_fetcher:
                        fetcher = RedditFetcher(source, db)
                        await asyncio.to_thread(fetcher.run)
                    elif source.platform == "rss" and self.settings.enable_rss_fetcher:
                        fetcher = RSSFetcher(source, db)
                        await asyncio.to_thread(fetcher.run)
                except Exception as e:
                    logger.error(f"Failed to fetch from {source.name}: {e}")
            
            logger.info("Content fetch completed")
        finally:
            db.close()
    
    async def calculate_scores(self):
        """Calculate heat and potential scores for unprocessed content."""
        logger.info("Starting scheduled score calculation")
        db = self._get_db()
        
        try:
            from src.models.content import Content
            
            # Get unprocessed content
            unprocessed = db.query(Content).filter(Content.is_processed == False).all()
            
            heat_scorer = HeatScorer()
            potential_scorer = PotentialScorer()
            
            for content in unprocessed:
                try:
                    # Calculate heat score
                    heat_result = heat_scorer.calculate(content)
                    if heat_result.success:
                        heat_scorer.save_score(content.id, heat_result, db)
                    
                    # Calculate potential score
                    potential_result = potential_scorer.calculate(content)
                    if potential_result.success:
                        potential_scorer.save_score(content.id, potential_result, db)
                    
                    # Mark as processed
                    content.is_processed = True
                    
                except Exception as e:
                    logger.error(f"Failed to calculate scores for content {content.id}: {e}")
            
            db.commit()
            logger.info(f"Score calculation completed for {len(unprocessed)} items")
        finally:
            db.close()
    
    async def generate_daily_brief(self):
        """Generate daily brief for yesterday."""
        logger.info("Starting scheduled brief generation")
        db = self._get_db()
        
        try:
            generator = BriefGenerator(db)
            yesterday = datetime.now() - timedelta(days=1)
            
            brief = generator.generate(brief_date=yesterday.date())
            logger.info(f"Daily brief generated: {brief.title}")
        finally:
            db.close()
    
    async def send_daily_brief(self):
        """Send the daily brief via configured channels."""
        logger.info("Starting scheduled brief sending")
        db = self._get_db()
        
        try:
            from src.models.brief import DailyBrief
            
            # Get today's brief
            today = datetime.now().date()
            brief = db.query(DailyBrief).filter(DailyBrief.brief_date == today).first()
            
            if not brief:
                logger.warning("No brief found for today, generating now")
                await self.generate_daily_brief()
                brief = db.query(DailyBrief).filter(DailyBrief.brief_date == today).first()
            
            if brief:
                publisher = BriefPublisher(db)
                results = publisher.publish_all(brief)
                logger.info(f"Brief sent: {results}")
            else:
                logger.error("Failed to generate or find brief for today")
        finally:
            db.close()
    
    def setup_jobs(self):
        """Configure all scheduled jobs."""
        # Content fetching every 4 hours
        self.scheduler.add_job(
            self.fetch_all_content,
            trigger=IntervalTrigger(minutes=self.settings.fetch_interval_minutes),
            id="fetch_all_content",
            name="Fetch content from all sources",
            replace_existing=True,
        )
        
        # Score calculation every 6 hours
        self.scheduler.add_job(
            self.calculate_scores,
            trigger=IntervalTrigger(hours=6),
            id="calculate_scores",
            name="Calculate heat and potential scores",
            replace_existing=True,
        )
        
        # Brief generation daily at configured hour
        self.scheduler.add_job(
            self.generate_daily_brief,
            trigger=CronTrigger(hour=self.settings.brief_generation_hour, minute=0),
            id="generate_daily_brief",
            name="Generate daily brief",
            replace_existing=True,
        )
        
        # Brief sending daily at configured hour:minute
        self.scheduler.add_job(
            self.send_daily_brief,
            trigger=CronTrigger(
                hour=self.settings.brief_send_hour,
                minute=self.settings.brief_send_minute
            ),
            id="send_daily_brief",
            name="Send daily brief",
            replace_existing=True,
        )
        
        logger.info("All scheduled jobs configured")
    
    def start(self):
        """Start the scheduler."""
        if self._running:
            logger.warning("Scheduler is already running")
            return
        
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        
        self.setup_jobs()
        self.scheduler.start()
        self._running = True
        
        logger.info("Task scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        if not self._running or not self.scheduler:
            logger.warning("Scheduler is not running")
            return
        
        self.scheduler.shutdown()
        self._running = False
        
        logger.info("Task scheduler stopped")
    
    def pause(self):
        """Pause all jobs."""
        if self.scheduler:
            self.scheduler.pause()
            logger.info("All jobs paused")
    
    def resume(self):
        """Resume all jobs."""
        if self.scheduler:
            self.scheduler.resume()
            logger.info("All jobs resumed")
    
    def get_job_status(self) -> dict:
        """Get status of all jobs."""
        if not self.scheduler:
            return {"status": "not_running", "jobs": []}
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            })
        
        return {
            "status": "running" if self._running else "stopped",
            "jobs": jobs,
        }


# Global scheduler instance
_scheduler_instance: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """Get or create global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = TaskScheduler()
    return _scheduler_instance


def start_scheduler():
    """Start the global scheduler."""
    scheduler = get_scheduler()
    scheduler.start()
    return scheduler


def stop_scheduler():
    """Stop the global scheduler."""
    global _scheduler_instance
    if _scheduler_instance:
        _scheduler_instance.stop()
        _scheduler_instance = None
