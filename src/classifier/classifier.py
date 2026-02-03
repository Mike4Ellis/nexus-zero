"""Content classification and tagging system."""

import re
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from src.models.content import Content
from src.models.tag import ContentTag, Tag


class ContentClassifier:
    """Classifies content into topics and extracts tags."""
    
    # Topic keywords for classification
    TOPIC_KEYWORDS = {
        "AI": [
            "人工智能", "AI", "machine learning", "deep learning", "neural network",
            "GPT", "LLM", "大模型", "ChatGPT", "Claude", "生成式AI", "AIGC",
            "stable diffusion", "midjourney", "prompt", "训练模型", "推理",
            "transformer", "BERT", "NLP", "计算机视觉", "CV", "强化学习",
        ],
        "科技": [
            "科技", "tech", "technology", "互联网", "internet", "软件", "software",
            "硬件", "hardware", "编程", "programming", "代码", "code",
            "开源", "open source", "GitHub", "开发者", "developer",
            "云计算", "cloud", "大数据", "big data", "区块链", "blockchain",
            "物联网", "IoT", "5G", "芯片", "半导体",
        ],
        "投资": [
            "投资", "investment", "股票", "stock", "基金", "fund", "理财",
            "finance", "金融", "经济", "economy", "市场", "market",
            "crypto", "加密货币", "比特币", "bitcoin", "以太坊", "eth",
            "A股", "港股", "美股", "IPO", "上市", "财报", "earnings",
            "量化", "quant", "交易策略", "trading", "收益率", "return",
        ],
        "生活": [
            "生活", "life", "lifestyle", "健康", "health", "健身", "fitness",
            "美食", "food", "旅行", "travel", "摄影", "photography",
            "家居", "home", "穿搭", "fashion", "护肤", "skincare",
            "读书", "reading", "电影", "movie", "音乐", "music",
            "宠物", "pet", "育儿", "parenting", "心理", "psychology",
        ],
        "娱乐": [
            "娱乐", "entertainment", "明星", "celebrity", "综艺", "show",
            "游戏", "game", "gaming", "电竞", "esports", "动漫", "anime",
            "八卦", "gossip", "吐槽", "搞笑", "funny", "meme",
            "追剧", "drama", "网剧", "短视频", "直播", "live",
        ],
        "设计": [
            "设计", "design", "UI", "UX", "界面", "interface", "视觉", "visual",
            "品牌", "branding", "插画", "illustration", "排版", "typography",
            "配色", "color", "Figma", "Sketch", "Photoshop", "创意", "creative",
            "艺术", "art", "建筑", "architecture", "室内", "interior",
        ],
    }
    
    # Sentiment keywords
    POSITIVE_WORDS = [
        "好", "棒", "优秀", "成功", "突破", "创新", "惊喜", "推荐", "喜欢",
        "good", "great", "excellent", "amazing", "awesome", "love", "best",
        "恭喜", "胜利", "增长", "提升", "解决", "完美", "赞", "👍", "❤️",
    ]
    
    NEGATIVE_WORDS = [
        "差", "糟糕", "失败", "问题", "bug", "错误", "失望", "讨厌", "恶心",
        "bad", "terrible", "awful", "hate", "worst", "fail", "error",
        "崩溃", "下降", "损失", "风险", "警告", "⚠️", "❌", "💔",
    ]
    
    def __init__(self, db: Session):
        self.db = db
        self._tag_cache: Dict[str, Tag] = {}
        self._load_tags()
    
    def _load_tags(self):
        """Load existing tags into cache."""
        tags = self.db.query(Tag).all()
        for tag in tags:
            self._tag_cache[tag.name] = tag
    
    def classify(self, content: Content) -> List[ContentTag]:
        """Classify content and return content-tag associations."""
        content_tags = []
        
        # Classify topic
        topic_tags = self._classify_topic(content)
        content_tags.extend(topic_tags)
        
        # Classify sentiment
        sentiment_tags = self._classify_sentiment(content)
        content_tags.extend(sentiment_tags)
        
        # Extract keywords
        keyword_tags = self._extract_keywords(content)
        content_tags.extend(keyword_tags)
        
        # Save to database
        for ct in content_tags:
            self.db.add(ct)
        
        content.is_processed = True
        self.db.commit()
        
        return content_tags
    
    def _classify_topic(self, content: Content) -> List[ContentTag]:
        """Classify content into topic categories."""
        text = f"{content.title or ''} {content.content or ''}".lower()
        content_tags = []
        
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                count = text.count(keyword.lower())
                if count > 0:
                    score += count
                    matched_keywords.append(keyword)
            
            # If significant match, add tag
            if score >= 1:
                tag = self._get_or_create_tag(topic, "topic")
                confidence = min(1.0, score / 3)  # Normalize confidence
                
                content_tag = ContentTag(
                    content_id=content.id,
                    tag_id=tag.id,
                    confidence=round(confidence, 2),
                    is_manual=False,
                )
                content_tags.append(content_tag)
        
        return content_tags
    
    def _classify_sentiment(self, content: Content) -> List[ContentTag]:
        """Classify content sentiment."""
        text = f"{content.title or ''} {content.content or ''}".lower()
        
        positive_score = sum(1 for word in self.POSITIVE_WORDS if word.lower() in text)
        negative_score = sum(1 for word in self.NEGATIVE_WORDS if word.lower() in text)
        
        content_tags = []
        
        if positive_score > negative_score:
            tag = self._get_or_create_tag("正面", "sentiment")
            confidence = min(1.0, (positive_score - negative_score) / 3)
            content_tags.append(ContentTag(
                content_id=content.id,
                tag_id=tag.id,
                confidence=round(confidence, 2),
                is_manual=False,
            ))
        elif negative_score > positive_score:
            tag = self._get_or_create_tag("负面", "sentiment")
            confidence = min(1.0, (negative_score - positive_score) / 3)
            content_tags.append(ContentTag(
                content_id=content.id,
                tag_id=tag.id,
                confidence=round(confidence, 2),
                is_manual=False,
            ))
        else:
            # Neutral
            tag = self._get_or_create_tag("中性", "sentiment")
            content_tags.append(ContentTag(
                content_id=content.id,
                tag_id=tag.id,
                confidence=0.8,
                is_manual=False,
            ))
        
        return content_tags
    
    def _extract_keywords(self, content: Content) -> List[ContentTag]:
        """Extract important keywords from content."""
        text = content.content or ""
        
        # Simple keyword extraction based on frequency and capitalization
        words = re.findall(r'\b[A-Za-z]{4,}\b|\b[\u4e00-\u9fa5]{2,}\b', text)
        word_freq: Dict[str, int] = {}
        
        for word in words:
            word = word.lower()
            if len(word) > 3:  # Filter short words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        top_keywords = [w for w, _ in sorted_words[:5]]
        
        content_tags = []
        for keyword in top_keywords:
            tag = self._get_or_create_tag(keyword, "keyword")
            content_tags.append(ContentTag(
                content_id=content.id,
                tag_id=tag.id,
                confidence=0.6,  # Lower confidence for auto-extracted keywords
                is_manual=False,
            ))
        
        return content_tags
    
    def _get_or_create_tag(self, name: str, category: str) -> Tag:
        """Get existing tag or create new one."""
        if name in self._tag_cache:
            return self._tag_cache[name]
        
        # Check database
        tag = self.db.query(Tag).filter(Tag.name == name).first()
        
        if not tag:
            # Create new tag
            tag = Tag(
                name=name,
                category=category,
                is_auto=True,
            )
            self.db.add(tag)
            self.db.commit()
            self.db.refresh(tag)
        
        self._tag_cache[name] = tag
        return tag
    
    def classify_batch(self, contents: List[Content]) -> int:
        """Classify multiple content items.
        
        Returns:
            Number of items classified
        """
        classified_count = 0
        
        for content in contents:
            try:
                self.classify(content)
                classified_count += 1
            except Exception as e:
                print(f"Failed to classify content {content.id}: {e}")
                continue
        
        return classified_count
    
    def classify_unprocessed(self, limit: Optional[int] = None) -> int:
        """Classify all unprocessed content.
        
        Returns:
            Number of items classified
        """
        query = self.db.query(Content).filter(Content.is_processed == False)
        
        if limit:
            query = query.limit(limit)
        
        contents = query.all()
        return self.classify_batch(contents)
