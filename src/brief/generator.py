"""Daily brief generation system."""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from jinja2 import Template
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.brief import DailyBrief
from src.models.content import Content
from src.models.score import Score
from src.models.tag import ContentTag, Tag


class BriefGenerator:
    """Generates daily briefs from curated content."""
    
    # Brief configuration
    HEAT_TOP_COUNT = 10
    POTENTIAL_TOP_COUNT = 5
    TOPICS_PER_CATEGORY = 3
    
    # Topic categories to include
    TOPIC_CATEGORIES = ["AI", "科技", "投资", "生活", "娱乐", "设计"]
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate(
        self,
        brief_date: Optional[date] = None,
        title: Optional[str] = None,
    ) -> DailyBrief:
        """Generate daily brief for specified date.
        
        Args:
            brief_date: Date for brief (default: yesterday)
            title: Custom title (default: auto-generated)
        """
        if brief_date is None:
            brief_date = date.today() - timedelta(days=1)
        
        # Calculate date range
        start_dt = datetime.combine(brief_date, datetime.min.time())
        end_dt = datetime.combine(brief_date + timedelta(days=1), datetime.min.time())
        
        # Get contents for the day
        contents = self._get_daily_contents(start_dt, end_dt)
        
        if not title:
            title = f"InfoFlow 每日简报 - {brief_date.strftime('%Y年%m月%d日')}"
        
        # Calculate statistics
        stats = self._calculate_stats(contents, brief_date)
        
        # Select featured content
        heat_top_ids = self._select_heat_top(contents)
        potential_ids = self._select_potential(contents)
        featured_ids = self._select_featured(heat_top_ids, potential_ids)
        
        # Get topic breakdown
        topic_breakdown = self._get_topic_breakdown(contents)
        
        # Generate content
        markdown_content = self._generate_markdown(
            title=title,
            brief_date=brief_date,
            stats=stats,
            heat_top_ids=heat_top_ids,
            potential_ids=potential_ids,
            featured_ids=featured_ids,
            topic_breakdown=topic_breakdown,
        )
        
        html_content = self._generate_html(
            title=title,
            brief_date=brief_date,
            stats=stats,
            heat_top_ids=heat_top_ids,
            potential_ids=potential_ids,
            featured_ids=featured_ids,
            topic_breakdown=topic_breakdown,
        )
        
        # Create or update brief
        brief = self.db.query(DailyBrief).filter(
            DailyBrief.brief_date == brief_date
        ).first()
        
        if brief:
            brief.title = title
            brief.stats = stats
            brief.total_contents = stats.get("total", 0)
            brief.featured_ids = featured_ids
            brief.heat_top_ids = heat_top_ids
            brief.potential_ids = potential_ids
            brief.topic_breakdown = topic_breakdown
            brief.markdown_content = markdown_content
            brief.html_content = html_content
        else:
            brief = DailyBrief(
                brief_date=brief_date,
                title=title,
                stats=stats,
                total_contents=stats.get("total", 0),
                featured_ids=featured_ids,
                heat_top_ids=heat_top_ids,
                potential_ids=potential_ids,
                topic_breakdown=topic_breakdown,
                markdown_content=markdown_content,
                html_content=html_content,
            )
            self.db.add(brief)
        
        # Mark contents as briefed
        for content_id in featured_ids:
            content = self.db.query(Content).get(content_id)
            if content:
                content.is_briefed = True
        
        self.db.commit()
        self.db.refresh(brief)
        
        return brief
    
    def _get_daily_contents(
        self,
        start_dt: datetime,
        end_dt: datetime,
    ) -> List[Content]:
        """Get all contents for the specified time range."""
        return self.db.query(Content).filter(
            Content.published_at >= start_dt,
            Content.published_at < end_dt,
            Content.is_deleted == False,
        ).all()
    
    def _calculate_stats(
        self,
        contents: List[Content],
        brief_date: date,
    ) -> Dict:
        """Calculate statistics for the brief."""
        if not contents:
            return {
                "total": 0,
                "platforms": {},
                "topics": {},
            }
        
        # Platform breakdown
        platforms = {}
        for content in contents:
            platform = content.platform
            platforms[platform] = platforms.get(platform, 0) + 1
        
        # Topic breakdown
        topics = {}
        for content in contents:
            content_tags = self.db.query(ContentTag).join(Tag).filter(
                ContentTag.content_id == content.id,
                Tag.category == "topic",
            ).all()
            for ct in content_tags:
                topic_name = ct.tag.name
                topics[topic_name] = topics.get(topic_name, 0) + 1
        
        return {
            "total": len(contents),
            "platforms": platforms,
            "topics": topics,
            "date": brief_date.isoformat(),
        }
    
    def _select_heat_top(self, contents: List[Content]) -> List[int]:
        """Select top content by heat score."""
        content_scores = []
        
        for content in contents:
            heat_score = self.db.query(Score.score).filter(
                Score.content_id == content.id,
                Score.score_type == "heat",
            ).scalar()
            
            if heat_score:
                content_scores.append((content.id, float(heat_score)))
        
        # Sort by score descending
        content_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N IDs
        return [cid for cid, _ in content_scores[:self.HEAT_TOP_COUNT]]
    
    def _select_potential(self, contents: List[Content]) -> List[int]:
        """Select high potential but low heat content."""
        candidates = []
        
        for content in contents:
            heat_score = self.db.query(Score.score).filter(
                Score.content_id == content.id,
                Score.score_type == "heat",
            ).scalar() or 0
            
            potential_score = self.db.query(Score.score).filter(
                Score.content_id == content.id,
                Score.score_type == "potential",
            ).scalar() or 0
            
            # High potential (>70) but low heat (<30)
            if potential_score > 70 and heat_score < 30:
                candidates.append((content.id, float(potential_score)))
        
        # Sort by potential score
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        return [cid for cid, _ in candidates[:self.POTENTIAL_TOP_COUNT]]
    
    def _select_featured(
        self,
        heat_top_ids: List[int],
        potential_ids: List[int],
    ) -> List[int]:
        """Select featured content combining heat and potential."""
        featured = list(dict.fromkeys(heat_top_ids + potential_ids))
        return featured[:15]  # Max 15 featured items
    
    def _get_topic_breakdown(self, contents: List[Content]) -> Dict[str, List[int]]:
        """Get content IDs grouped by topic."""
        breakdown = {}
        
        for topic in self.TOPIC_CATEGORIES:
            tag = self.db.query(Tag).filter(
                Tag.name == topic,
                Tag.category == "topic",
            ).first()
            
            if not tag:
                continue
            
            # Get top content IDs for this topic
            content_ids = self.db.query(ContentTag.content_id).filter(
                ContentTag.tag_id == tag.id,
            ).limit(self.TOPICS_PER_CATEGORY).all()
            
            breakdown[topic] = [cid for (cid,) in content_ids]
        
        return breakdown
    
    def _generate_markdown(
        self,
        title: str,
        brief_date: date,
        stats: Dict,
        heat_top_ids: List[int],
        potential_ids: List[int],
        featured_ids: List[int],
        topic_breakdown: Dict[str, List[int]],
    ) -> str:
        """Generate Markdown format brief."""
        template_str = """# {{ title }}

> {{ brief_date.strftime('%Y年%m月%d日') }} | 共收录 {{ stats.total }} 条内容

---

## 📊 今日概览

{% if stats.platforms %}
**来源分布：**
{% for platform, count in stats.platforms.items() %}
- {{ platform }}: {{ count }} 条
{% endfor %}
{% endif %}

{% if stats.topics %}
**主题分布：**
{% for topic, count in stats.topics.items() %}
- {{ topic }}: {{ count }} 条
{% endfor %}
{% endif %}

---

## 🔥 热门精选

{% for content_id in heat_top_ids %}
{{ loop.index }}. [内容ID: {{ content_id }}]
{% endfor %}

---

## 💎 潜力发现

{% for content_id in potential_ids %}
{{ loop.index }}. [内容ID: {{ content_id }}]
   - 高潜力低热度内容，值得关注
{% endfor %}

---

## 📚 按主题浏览

{% for topic, content_ids in topic_breakdown.items() %}
### {{ topic }}
{% for content_id in content_ids %}
- [内容ID: {{ content_id }}]
{% endfor %}

{% endfor %}

---

*由 InfoFlow Platform 自动生成*
"""
        
        template = Template(template_str)
        return template.render(
            title=title,
            brief_date=brief_date,
            stats=stats,
            heat_top_ids=heat_top_ids,
            potential_ids=potential_ids,
            featured_ids=featured_ids,
            topic_breakdown=topic_breakdown,
        )
    
    def _generate_html(
        self,
        title: str,
        brief_date: date,
        stats: Dict,
        heat_top_ids: List[int],
        potential_ids: List[int],
        featured_ids: List[int],
        topic_breakdown: Dict[str, List[int]],
    ) -> str:
        """Generate HTML format brief."""
        # Simple HTML template
        html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }
        h1 { color: #1a1a1a; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; }
        h2 { color: #333; margin-top: 30px; }
        h3 { color: #555; }
        .meta { color: #666; font-size: 14px; margin-bottom: 20px; }
        .stats { background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0; }
        .heat { background: #fff3e0; padding: 15px; border-radius: 8px; margin: 20px 0; }
        .potential { background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0; }
        ul { padding-left: 20px; }
        li { margin: 8px 0; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0; color: #999; font-size: 12px; text-align: center; }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>
    <div class="meta">{{ brief_date.strftime('%Y年%m月%d日') }} | 共收录 {{ stats.total }} 条内容</div>
    
    <div class="stats">
        <h2>📊 今日概览</h2>
        {% if stats.platforms %}
        <p><strong>来源分布：</strong></p>
        <ul>
        {% for platform, count in stats.platforms.items() %}
            <li>{{ platform }}: {{ count }} 条</li>
        {% endfor %}
        </ul>
        {% endif %}
    </div>
    
    <div class="heat">
        <h2>🔥 热门精选</h2>
        <ol>
        {% for content_id in heat_top_ids %}
            <li>内容ID: {{ content_id }}</li>
        {% endfor %}
        </ol>
    </div>
    
    <div class="potential">
        <h2>💎 潜力发现</h2>
        <ol>
        {% for content_id in potential_ids %}
            <li>内容ID: {{ content_id }} - 高潜力低热度内容</li>
        {% endfor %}
        </ol>
    </div>
    
    <h2>📚 按主题浏览</h2>
    {% for topic, content_ids in topic_breakdown.items() %}
    <h3>{{ topic }}</h3>
    <ul>
    {% for content_id in content_ids %}
        <li>内容ID: {{ content_id }}</li>
    {% endfor %}
    </ul>
    {% endfor %}
    
    <div class="footer">
        由 InfoFlow Platform 自动生成
    </div>
</body>
</html>"""
        
        template = Template(html_template)
        return template.render(
            title=title,
            brief_date=brief_date,
            stats=stats,
            heat_top_ids=heat_top_ids,
            potential_ids=potential_ids,
            featured_ids=featured_ids,
            topic_breakdown=topic_breakdown,
        )
