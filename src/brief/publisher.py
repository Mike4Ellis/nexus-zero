"""Brief publisher for multiple channels (Telegram, Email)."""

import os
import subprocess
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
        
        lines.append("\n_由 Nexus Zero 自动生成_")
        
        return "\n".join(lines)
    
    def publish_email(self, brief: DailyBrief) -> bool:
        """Publish brief via Email using gog CLI.
        
        Returns:
            True if successful, False otherwise
        """
        # Get email configuration from environment
        to_email = os.getenv("NEXUS_EMAIL_TO")
        gog_account = os.getenv("GOG_ACCOUNT")
        
        if not to_email:
            print("Email recipient not configured (NEXUS_EMAIL_TO)")
            return False
        
        if not gog_account:
            print("GOG account not configured")
            return False
        
        try:
            # Generate HTML email content
            html_content = self._format_email_html(brief)
            
            # Use gog to send email
            result = subprocess.run(
                [
                    "gog", "gmail", "send",
                    "--to", to_email,
                    "--subject", brief.title,
                    "--body-html", html_content,
                    "--account", gog_account,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            
            if result.returncode == 0:
                brief.email_sent = True
                brief.sent_at = brief.sent_at or datetime.utcnow()
                self.db.commit()
                print(f"Email sent successfully to {to_email}")
                return True
            else:
                print(f"Failed to send email: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("Email sending timed out")
            return False
        except FileNotFoundError:
            print("gog CLI not found. Please install gog: brew install steipete/tap/gogcli")
            return False
        except Exception as e:
            print(f"Failed to publish email: {e}")
            return False
    
    def _format_email_html(self, brief: DailyBrief) -> str:
        """Format brief as HTML email."""
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='utf-8'>",
            "<style>",
            "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }",
            "h1 { color: #1a1a1a; border-bottom: 2px solid #4a90d9; padding-bottom: 10px; }",
            ".stats { background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0; }",
            ".section { margin: 25px 0; }",
            ".section h2 { color: #4a90d9; font-size: 18px; }",
            ".content-item { padding: 10px; border-left: 3px solid #4a90d9; margin: 10px 0; background: #fafafa; }",
            ".platform { display: inline-block; background: #4a90d9; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px; margin-right: 5px; }",
            ".footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>📰 {brief.title}</h1>",
            "<div class='stats'>",
            f"<strong>📊 今日收录：{brief.total_contents or 0} 条内容</strong>",
            "</div>",
        ]
        
        # Add platform breakdown
        if brief.stats and brief.stats.get("platforms"):
            html_parts.append("<div class='section'>")
            html_parts.append("<h2>📱 来源分布</h2>")
            html_parts.append("<ul>")
            for platform, count in brief.stats["platforms"].items():
                html_parts.append(f"<li><span class='platform'>{platform}</span> {count} 条</li>")
            html_parts.append("</ul>")
            html_parts.append("</div>")
        
        # Add heat top section
        if brief.heat_top_ids:
            html_parts.append("<div class='section'>")
            html_parts.append(f"<h2>🔥 热门精选 ({len(brief.heat_top_ids)} 条)</h2>")
            for i, content_id in enumerate(brief.heat_top_ids[:5], 1):
                html_parts.append(f"<div class='content-item'>{i}. 内容 ID: {content_id}</div>")
            html_parts.append("</div>")
        
        # Add potential section
        if brief.potential_ids:
            html_parts.append("<div class='section'>")
            html_parts.append(f"<h2>💎 潜力发现 ({len(brief.potential_ids)} 条)</h2>")
            for i, content_id in enumerate(brief.potential_ids[:3], 1):
                html_parts.append(f"<div class='content-item'>{i}. 内容 ID: {content_id}</div>")
            html_parts.append("</div>")
        
        # Footer
        html_parts.append("<div class='footer'>")
        html_parts.append("<p>由 <strong>Nexus Zero</strong> 智能信息聚合平台自动生成</p>")
        html_parts.append(f"<p>生成时间：{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>")
        html_parts.append("</div>")
        
        html_parts.append("</body>")
        html_parts.append("</html>")
        
        return "".join(html_parts)
    
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
