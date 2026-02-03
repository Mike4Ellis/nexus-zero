"""Brief publisher for multiple channels (Telegram, Email)."""

import os
from typing import Optional

from sqlalchemy.orm import Session

from src.models.brief import DailyBrief


class BriefPublisher:
    """Publishes daily briefs to various channels."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def publish_telegram(self, brief: DailyBrief) -> bool:
        """Publish brief to Telegram channel.
        
        Returns:
            True if successful, False otherwise
        """
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not bot_token or not chat_id:
            print("Telegram credentials not configured")
            return False
        
        try:
            # Use python-telegram-bot or direct API call
            import requests
            
            message = self._format_telegram_message(brief)
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False,
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                brief.telegram_sent = True
                brief.sent_at = brief.sent_at or datetime.utcnow()
                self.db.commit()
                return True
            else:
                print(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Failed to publish to Telegram: {e}")
            return False
    
    def _format_telegram_message(self, brief: DailyBrief) -> str:
        """Format brief for Telegram (Markdown)."""
        lines = [
            f"📰 *{brief.title}*",
            "",
            f"📊 今日收录：{brief.total_contents} 条内容",
        ]
        
        # Add platform breakdown
        if brief.stats and "platforms" in brief.stats:
            lines.append("\n*来源分布：*")
            for platform, count in brief.stats["platforms"].items():
                lines.append(f"• {platform}: {count} 条")
        
        # Add heat top preview
        if brief.heat_top_ids:
            lines.append(f"\n🔥 *热门精选* ({len(brief.heat_top_ids)} 条)")
            for i, content_id in enumerate(brief.heat_top_ids[:5], 1):
                lines.append(f"{i}. [内容ID: {content_id}]")
        
        # Add potential preview
        if brief.potential_ids:
            lines.append(f"\n💎 *潜力发现* ({len(brief.potential_ids)} 条)")
            for i, content_id in enumerate(brief.potential_ids[:3], 1):
                lines.append(f"{i}. [内容ID: {content_id}]")
        
        lines.append("\n_由 InfoFlow Platform 自动生成_")
        
        return "\n".join(lines)
    
    def publish_email(self, brief: DailyBrief) -> bool:
        """Publish brief via Email.
        
        Returns:
            True if successful, False otherwise
        """
        # Email publishing will be implemented with gog skill
        # For now, placeholder
        print("Email publishing not yet implemented (requires gog skill)")
        return False
    
    def publish_all(self, brief: DailyBrief) -> dict:
        """Publish to all configured channels.
        
        Returns:
            Dict with channel names as keys and success status as values
        """
        results = {}
        
        # Telegram
        if os.getenv("TELEGRAM_BOT_TOKEN"):
            results["telegram"] = self.publish_telegram(brief)
        
        # Email
        if os.getenv("GOG_ACCOUNT"):
            results["email"] = self.publish_email(brief)
        
        return results


# Import at the end to avoid circular imports
from datetime import datetime
