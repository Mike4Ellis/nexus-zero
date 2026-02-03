# InfoFlow Platform - AGENTS.md

## 项目信息
- **名称**: InfoFlow Platform (信息流聚合与筛选平台)
- **技术栈**: Python 3.11+, FastAPI, SQLAlchemy, PostgreSQL, APScheduler
- **分支**: ralph/infoflow-platform

## 开发规范

### 代码质量
- 使用 `ruff` 进行代码格式化和 lint
- 使用 `mypy` 进行类型检查
- 所有代码必须通过 typecheck: `mypy src/`

### 测试回压
```bash
# 类型检查
mypy src/

# 代码格式检查
ruff check src/

# 运行测试
pytest tests/
```

### 项目结构
```
info-flow-platform/
├── src/
│   ├── __init__.py
│   ├── models/          # SQLAlchemy ORM 模型
│   ├── fetcher/         # 内容抓取器 (X, Reddit, RSS)
│   ├── scorer/          # 评分算法 (热度, 潜力)
│   ├── classifier/      # 内容分类与标签
│   ├── brief/           # 简报生成
│   ├── web/             # Web API (FastAPI)
│   ├── utils/           # 工具函数
│   └── config.py        # 配置管理
├── tests/
├── alembic/             # 数据库迁移
├── specs/               # 技术规格文档
├── agents/
│   └── prd.json         # PRD 用户故事
├── IMPLEMENTATION_PLAN.md  # 实现计划 (由Ralph维护)
├── PROMPT.md            # 当前模式提示词
└── AGENTS.md            # 本文件
```

### 依赖管理
- 使用 `pyproject.toml` + `poetry` 或 `pip`
- 主要依赖:
  - fastapi, uvicorn
  - sqlalchemy, alembic, psycopg2-binary
  - apscheduler
  - praw (Reddit)
  - tweepy (X/Twitter)
  - feedparser (RSS)
  - jinja2 (模板)
  - pandas, openpyxl (数据导出)

### Git 提交规范
- 使用 conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- 每个用户故事完成后提交

### 环境变量
```bash
# 数据库
DATABASE_URL=postgresql://user:pass@localhost/infoflow

# API Keys (按需配置)
X_API_KEY=xxx
X_API_SECRET=xxx
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx
TELEGRAM_BOT_TOKEN=xxx

# 邮件 (gog skill)
GOG_ACCOUNT=your@gmail.com
```
