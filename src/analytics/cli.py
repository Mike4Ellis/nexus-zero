"""CLI for analytics and reporting.

Usage:
    python -m src.analytics report          # Generate JSON report
    python -m src.analytics daily           # Generate daily report
    python -m src.analytics export-excel    # Export to Excel
    python -m src.analytics stats           # Show quick stats
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from src.database import SessionLocal
from src.analytics.stats import (
    AnalyticsReporter,
    generate_daily_report,
    export_to_excel,
    export_to_json,
)


def cmd_report(args):
    """Generate comprehensive analytics report."""
    db = SessionLocal()
    try:
        reporter = AnalyticsReporter(db)
        
        start_date = None
        if args.days:
            start_date = datetime.utcnow() - timedelta(days=args.days)
        
        report = reporter.generate_report(start_date=start_date)
        
        if args.output:
            export_to_json(db, args.output, start_date)
            print(f"✅ Report exported to: {args.output}")
        else:
            print(json.dumps(report, indent=2, default=str))
    finally:
        db.close()


def cmd_daily(args):
    """Generate daily report."""
    db = SessionLocal()
    try:
        date = None
        if args.date:
            date = datetime.strptime(args.date, "%Y-%m-%d")
        
        report = generate_daily_report(db, date)
        print(json.dumps(report, indent=2, default=str))
    finally:
        db.close()


def cmd_export_excel(args):
    """Export content to Excel."""
    db = SessionLocal()
    try:
        start_date = None
        end_date = None
        
        if args.start_date:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        if args.end_date:
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d") + timedelta(days=1)
        
        output_path = args.output or f"exports/nexus_zero_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        result = export_to_excel(db, output_path, start_date, end_date)
        print(f"✅ Exported {result}")
        print(f"   Total records: {len(db.query(Content).all())}")
    except ImportError as e:
        print(f"❌ {e}")
        sys.exit(1)
    finally:
        db.close()


def cmd_stats(args):
    """Show quick statistics."""
    db = SessionLocal()
    try:
        reporter = AnalyticsReporter(db)
        stats = reporter.get_overview_stats()
        
        print("\n📊 Nexus Zero Statistics")
        print("=" * 40)
        print(f"Total Contents: {stats['total_contents']}")
        print(f"Total Sources: {stats['total_sources']}")
        print(f"Active Sources: {stats['active_sources']}")
        print(f"\nAverage Scores:")
        print(f"  Heat: {stats['average_scores']['heat']}")
        print(f"  Potential: {stats['average_scores']['potential']}")
        print(f"\nPlatform Breakdown:")
        for platform, count in stats['platform_breakdown'].items():
            print(f"  {platform}: {count}")
        print()
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Nexus Zero Analytics CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # report
    report_parser = subparsers.add_parser("report", help="Generate analytics report")
    report_parser.add_argument("--days", type=int, help="Number of days to include")
    report_parser.add_argument("--output", "-o", help="Output JSON file path")
    report_parser.set_defaults(func=cmd_report)
    
    # daily
    daily_parser = subparsers.add_parser("daily", help="Generate daily report")
    daily_parser.add_argument("--date", help="Date (YYYY-MM-DD), default: yesterday")
    daily_parser.set_defaults(func=cmd_daily)
    
    # export-excel
    excel_parser = subparsers.add_parser("export-excel", help="Export to Excel")
    excel_parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    excel_parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    excel_parser.add_argument("--output", "-o", help="Output file path")
    excel_parser.set_defaults(func=cmd_export_excel)
    
    # stats
    stats_parser = subparsers.add_parser("stats", help="Show quick statistics")
    stats_parser.set_defaults(func=cmd_stats)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
