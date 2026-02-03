"""CLI for managing the task scheduler.

Usage:
    python -m src.scheduler start    # Start scheduler
    python -m src.scheduler stop     # Stop scheduler
    python -m src.scheduler status   # Show job status
    python -m src.scheduler pause    # Pause all jobs
    python -m src.scheduler resume   # Resume all jobs
"""

import argparse
import asyncio
import logging
import sys

from .scheduler import get_scheduler, start_scheduler, stop_scheduler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def cmd_start(args):
    """Start the scheduler."""
    scheduler = start_scheduler()
    
    print("✅ Scheduler started")
    print("\nScheduled jobs:")
    status = scheduler.get_job_status()
    for job in status["jobs"]:
        print(f"  • {job['name']} (next: {job['next_run']})")
    
    print("\nPress Ctrl+C to stop")
    
    try:
        # Keep running
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\n\nStopping scheduler...")
        stop_scheduler()
        print("✅ Scheduler stopped")


def cmd_stop(args):
    """Stop the scheduler."""
    stop_scheduler()
    print("✅ Scheduler stopped")


def cmd_status(args):
    """Show scheduler status."""
    scheduler = get_scheduler()
    status = scheduler.get_job_status()
    
    print(f"Status: {status['status']}")
    
    if status["jobs"]:
        print("\nJobs:")
        for job in status["jobs"]:
            next_run = job['next_run'][:19] if job['next_run'] else "N/A"
            print(f"  • {job['name']}")
            print(f"    Next run: {next_run}")
    else:
        print("\nNo jobs configured")


def cmd_pause(args):
    """Pause all jobs."""
    scheduler = get_scheduler()
    scheduler.pause()
    print("⏸️  All jobs paused")


def cmd_resume(args):
    """Resume all jobs."""
    scheduler = get_scheduler()
    scheduler.resume()
    print("▶️  All jobs resumed")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Nexus Zero Task Scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.scheduler start
  python -m src.scheduler status
  python -m src.scheduler pause
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # start
    start_parser = subparsers.add_parser("start", help="Start the scheduler")
    start_parser.set_defaults(func=cmd_start)
    
    # stop
    stop_parser = subparsers.add_parser("stop", help="Stop the scheduler")
    stop_parser.set_defaults(func=cmd_stop)
    
    # status
    status_parser = subparsers.add_parser("status", help="Show scheduler status")
    status_parser.set_defaults(func=cmd_status)
    
    # pause
    pause_parser = subparsers.add_parser("pause", help="Pause all jobs")
    pause_parser.set_defaults(func=cmd_pause)
    
    # resume
    resume_parser = subparsers.add_parser("resume", help="Resume all jobs")
    resume_parser.set_defaults(func=cmd_resume)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
