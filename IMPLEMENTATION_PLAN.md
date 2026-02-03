# Nexus Zero - Implementation Plan

> **Nexus**: 连接所有数据流的中心节点  
> **Zero**: 最有价值/最为优质的信息筛选中心  
> 
> Branch: `main`  
> Repository: https://github.com/Mike4Ellis/nexus-zero

---

## 1. Database Schema Design

### 1.1 Entity Relationship Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   sources   │────▶│  contents   │◀────│    tags     │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │                    ▲
                           ▼                    │
                    ┌─────────────┐     ┌─────────────┐
                    │   scores    │     │ content_tags│
                    └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ daily_briefs│
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ fetch_logs  │
                    └─────────────┘
```

### 1.2 Table Definitions

#### `sources` - 内容源配置表
```sql
CREATE TABLE sources (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,           -- 源名称 (e.g., "X-Tech", "Reddit-AI")
    platform        VARCHAR(50) NOT NULL,            -- 平台类型: x, reddit, rss, xiaohongshu
    config          JSONB NOT NULL DEFAULT '{}',     -- 平台特定配置
    is_active       BOOLEAN DEFAULT TRUE,
    fetch_interval  INTEGER DEFAULT 240,             -- 抓取间隔(分钟)
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

#### `contents` - 内容主表
```sql
CREATE TABLE contents (
    id              SERIAL PRIMARY KEY,
    source_id       INTEGER REFERENCES sources(id),
    platform        VARCHAR(50) NOT NULL,            -- 来源平台
    external_id     VARCHAR(255) NOT NULL,           -- 平台内容ID
    title           TEXT,                            -- 标题(可选)
    content         TEXT NOT NULL,                   -- 内容正文
    author          VARCHAR(255),                    -- 作者
    author_id       VARCHAR(255),                    -- 作者平台ID
    url             TEXT,                            -- 原始链接
    published_at    TIMESTAMP NOT NULL,              -- 发布时间
    
    -- 互动数据(各平台原始值)
    raw_metrics     JSONB DEFAULT '{}',              -- {views, likes, reposts, comments, bookmarks}
    
    -- 媒体附件
    media_urls      JSONB DEFAULT '[]',              -- 图片/视频URL列表
    
    -- 处理状态
    is_processed    BOOLEAN DEFAULT FALSE,           -- 是否已评分/分类
    is_briefed      BOOLEAN DEFAULT FALSE,           -- 是否已入选简报
    
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(platform, external_id)
);

CREATE INDEX idx_contents_platform ON contents(platform);
CREATE INDEX idx_contents_published_at ON contents(published_at DESC);
CREATE INDEX idx_contents_is_processed ON contents(is_processed);
```

#### `scores` - 内容评分表
```sql
CREATE TABLE scores (
    id              SERIAL PRIMARY KEY,
    content_id      INTEGER REFERENCES contents(id) ON DELETE CASCADE,
    score_type      VARCHAR(20) NOT NULL,            -- 'heat' | 'potential'
    score           DECIMAL(5,2) NOT NULL,           -- 0-100
    
    -- 评分因子详情(用于调试和优化)
    factors         JSONB DEFAULT '{}',              -- {factor_name: value, weight}
    
    calculated_at   TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(content_id, score_type)
);

CREATE INDEX idx_scores_type_score ON scores(score_type, score DESC);
CREATE INDEX idx_scores_content_id ON scores(content_id);
```

#### `tags` - 标签定义表
```sql
CREATE TABLE tags (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL UNIQUE,    -- 标签名
    category        VARCHAR(50),                     -- 分类: topic, sentiment, entity, tech, custom
    description     TEXT,
    color           VARCHAR(7),                      -- 显示颜色 #RRGGBB
    is_auto         BOOLEAN DEFAULT TRUE,            -- 是否自动标签
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 预置标签
INSERT INTO tags (name, category) VALUES
('AI', 'topic'), ('科技', 'topic'), ('投资', 'topic'),
('生活', 'topic'), ('娱乐', 'topic'), ('设计', 'topic'),
('正面', 'sentiment'), ('负面', 'sentiment'), ('中性', 'sentiment');
```

#### `content_tags` - 内容标签关联表
```sql
CREATE TABLE content_tags (
    id              SERIAL PRIMARY KEY,
    content_id      INTEGER REFERENCES contents(id) ON DELETE CASCADE,
    tag_id          INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    confidence      DECIMAL(4,3) DEFAULT 1.0,        -- 置信度(自动标签)
    is_manual       BOOLEAN DEFAULT FALSE,           -- 是否手动添加
    created_at      TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(content_id, tag_id)
);

CREATE INDEX idx_content_tags_tag ON content_tags(tag_id);
CREATE INDEX idx_content_tags_content ON content_tags(content_id);
```

#### `daily_briefs` - 每日简报表
```sql
CREATE TABLE daily_briefs (
    id              SERIAL PRIMARY KEY,
    brief_date      DATE NOT NULL UNIQUE,            -- 简报日期
    title           VARCHAR(255) NOT NULL,           -- 简报标题
    
    -- 统计摘要
    stats           JSONB DEFAULT '{}',              -- {total: N, platforms: {}, topics: {}}
    
    -- 内容构成
    featured_ids    INTEGER[] DEFAULT '{}',          -- 精选内容IDs
    heat_top_ids    INTEGER[] DEFAULT '{}',          -- 热度Top IDs
    potential_ids   INTEGER[] DEFAULT '{}',          -- 潜力内容IDs
    
    -- 输出
    markdown_content TEXT,                           -- Markdown格式内容
    html_content    TEXT,                            -- HTML格式内容
    
    -- 发送状态
    telegram_sent   BOOLEAN DEFAULT FALSE,
    email_sent      BOOLEAN DEFAULT FALSE,
    sent_at         TIMESTAMP,
    
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_daily_briefs_date ON daily_briefs(brief_date DESC);
```

#### `fetch_logs` - 抓取日志表
```sql
CREATE TABLE fetch_logs (
    id              SERIAL PRIMARY KEY,
    source_id       INTEGER REFERENCES sources(id),
    platform        VARCHAR(50) NOT NULL,
    
    -- 执行信息
    started_at      TIMESTAMP DEFAULT NOW(),
    ended_at        TIMESTAMP,
    status          VARCHAR(20) NOT NULL,            -- 'running' | 'success' | 'failed' | 'partial'
    
    -- 结果统计
    items_fetched   INTEGER DEFAULT 0,
    items_new       INTEGER DEFAULT 0,
    items_updated   INTEGER DEFAULT 0,
    
    -- 错误信息
    error_message   TEXT,
    error_trace     TEXT,
    
    -- 请求详情(用于调试)
    request_params  JSONB DEFAULT '{}',
    response_meta   JSONB DEFAULT '{}'
);

CREATE INDEX idx_fetch_logs_source ON fetch_logs(source_id, started_at DESC);
CREATE INDEX idx_fetch_logs_status ON fetch_logs(status);
```

---

## 2. US-001 Task Breakdown

### US-001: 初始化项目结构与数据库Schema ✅ COMPLETED

| # | Task | Description | Status | Notes |
|---|------|-------------|--------|-------|
| 1.1 | **创建项目目录结构** | 创建 `src/{fetcher,scorer,classifier,brief,web,models,utils}` | ✅ Done | All directories created |
| 1.2 | **配置Python环境** | 创建 `pyproject.toml`, 定义依赖 | ✅ Done | Full dependencies configured |
| 1.3 | **设计SQLAlchemy ORM模型** | 为7张表创建模型类 | ✅ Done | All 7 models implemented |
| 1.4 | **配置Alembic迁移** | 初始化Alembic，创建迁移脚本 | ⏳ Pending | Next: run `alembic init` |
| 1.5 | **运行初始迁移** | 执行 `alembic upgrade head` | ⏳ Pending | Requires database setup |
| 1.6 | **配置类型检查与CI** | 添加 mypy/ruff 配置 | ✅ Done | Configured in pyproject.toml |

**Completed by:** Gre (manual implementation due to 429 quota limits)

**Files Created:**
- `pyproject.toml` - Project config with dependencies
- `.env.example` - Environment template
- `src/config.py` - Pydantic settings
- `src/database.py` - SQLAlchemy engine & sessions
- `src/models/{base,source,content,score,tag,brief,log}.py` - All ORM models

**Next Steps:**
1. Run `pip install -e ".[dev]"` to install dependencies
2. Run `alembic init alembic` to setup migrations
3. Create initial migration script
4. Run `alembic upgrade head` to create tables

---

## 3. Five-Phase Implementation Approach

### Phase 1: Foundation (Week 1) ✅ IN PROGRESS
**Goal:** 建立项目骨架，完成数据库和基础架构

**Key Deliverables:**
- ✅ 项目目录结构和依赖配置
- ✅ 7张表的ORM模型
- ⏳ Alembic迁移和数据库初始化
- ✅ 基础工具类: 数据库连接、配置管理
- ✅ 类型检查配置

**Current Status:** Core structure complete, pending migration setup

---

### Phase 2: Data Collection (Week 2-3)
**Goal:** 实现多平台内容抓取器

**Implementation Strategy:**
1. **抽象基类设计** (`src/fetcher/base.py`)
   - `BaseFetcher` 定义统一接口: `fetch()`, `parse()`, `save()`
   - 通用功能: 重试机制、速率限制、错误处理

2. **平台实现顺序:**
   - X (Twitter): 使用 `tweepy` 或官方API v2
   - Reddit: 使用 `praw`
   - RSS: 使用 `feedparser`
   - 小红书: 调研期延后(US-013)

3. **增量抓取机制:**
   - 每个source记录 `last_fetch_at` 和 `last_cursor`
   - 使用 `fetch_logs` 追踪执行状态

---

### Phase 3: Intelligence Engine (Week 4-5)
**Goal:** 实现评分算法和自动分类

**3.1 热度评分 (Heat Score)**
```python
# 核心公式
heat_score = normalize(interactions) * time_decay(hours_since_publish)

# 互动归一化
interactions = w1*views + w2*likes + w3*reposts + w4*comments + w5*bookmarks

# 时间衰减 (24h内满分，7天后10%)
decay = max(0.1, 1 - (hours / 168))
```

**3.2 潜力评分 (Potential Score)**
```python
potential_score = (
    content_quality * 0.3 +      # NLP分析
    author_weight * 0.2 +        # 作者历史表现
    engagement_rate * 0.25 +     # 互动率
    growth_trend * 0.15 +        # 增速
    scarcity * 0.1               # 领域稀缺性
)
```

---

### Phase 4: Output Generation (Week 6)
**Goal:** 实现简报生成和多渠道推送

**4.1 简报生成流程:**
1. 查询昨日新增内容
2. 按综合评分排序 (heat * 0.6 + potential * 0.4)
3. 分类选取: 每个topic取Top 3
4. 潜力推荐: potential > 70 且 heat < 30
5. 使用Jinja2渲染模板

**4.2 推送渠道:**
| Channel | Format | Library |
|---------|--------|---------|
| Telegram | Markdown | `python-telegram-bot` |
| Email | HTML + Text | `gog` skill integration |

---

### Phase 5: Automation & Polish (Week 7-8)
**Goal:** 任务调度、监控和Web界面

**5.1 任务调度 (APScheduler):**
```python
scheduler.add_job(fetch_all, 'interval', hours=4)
scheduler.add_job(calculate_scores, 'cron', hour='*/6')
scheduler.add_job(generate_brief, 'cron', hour=8, minute=0)
scheduler.add_job(send_brief, 'cron', hour=8, minute=30)
```

**5.2 Web管理界面 (Next.js + FastAPI):**
- 今日简报: 卡片式展示，支持分享
- 历史归档: 日历视图，日期跳转
- 内容搜索: 全文检索 + 多维度筛选
- 统计面板: 来源趋势、热门标签、评分分布

---

## Appendix: Technology Stack Summary

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ |
| Database | PostgreSQL 15+ / SQLite (dev) |
| ORM | SQLAlchemy 2.0 |
| Migration | Alembic |
| Config | Pydantic Settings |
| Testing | pytest + pytest-asyncio |
| Scheduling | APScheduler |
| Frontend | Next.js 14 + Tailwind CSS |
| API | FastAPI |
| Type Check | mypy |
| Lint | ruff |

---

STATUS: PHASE1_IN_PROGRESS
