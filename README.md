# Nexus Zero - 智能信息聚合与筛选中心

> **Nexus**: 连接所有数据流的中心节点  
> **Zero**: 最有价值/最为优质的信息筛选中心

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)

## 🎯 项目概述

Nexus Zero 是一个智能信息聚合平台，通过多源抓取、AI评分、自动分类，帮助用户从海量信息中筛选出最有价值的内容。

### 核心功能

- 🔥 **双指标挖掘**：热度评分 + 潜力评分，发现热门内容和潜在爆款
- 📊 **每日简报**：自动生成结构化日报，支持多渠道推送
- 🌐 **多平台支持**：X/Twitter、Reddit、RSS、小红书
- 🤖 **任务调度**：自动化抓取、评分、生成简报
- 💻 **Web管理界面**：可视化数据看板，历史归档浏览

## 📁 项目结构

```
nexus-zero/
├── src/                          # 后端源码 (Python)
│   ├── api/                      # FastAPI REST API
│   │   └── main.py               # API入口，包含所有端点
│   ├── fetcher/                  # 内容抓取器
│   │   ├── base.py               # 抓取器基类
│   │   ├── x_fetcher.py          # X/Twitter抓取器
│   │   ├── reddit_fetcher.py     # Reddit抓取器
│   │   ├── rss_fetcher.py        # RSS抓取器
│   │   └── xiaohongshu_fetcher.py # 小红书抓取器
│   ├── scorer/                   # 评分算法
│   │   ├── base.py               # 评分器基类
│   │   ├── heat_scorer.py        # 热度评分
│   │   └── potential_scorer.py   # 潜力评分
│   ├── classifier/               # 内容分类
│   │   └── auto_classifier.py    # 自动标签分类
│   ├── brief/                    # 简报生成
│   │   ├── generator.py          # 简报生成器
│   │   └── publisher.py          # 多渠道发布
│   ├── scheduler/                # 任务调度
│   │   ├── scheduler.py          # APScheduler封装
│   │   └── cli.py                # 命令行工具
│   ├── models/                   # SQLAlchemy ORM模型
│   │   ├── base.py               # 基础模型
│   │   ├── source.py             # 内容源模型
│   │   ├── content.py            # 内容模型
│   │   ├── score.py              # 评分模型
│   │   ├── tag.py                # 标签模型
│   │   ├── brief.py              # 简报模型
│   │   └── log.py                # 日志模型
│   ├── memory_db.py              # 内存数据库(开发/测试)
│   ├── database.py               # 数据库连接配置
│   └── config.py                 # 应用配置
├── web/                          # 前端 (Next.js + TypeScript)
│   ├── src/
│   │   ├── app/                  # Next.js App Router
│   │   ├── components/           # React组件
│   │   │   ├── BriefCard.tsx     # 简报卡片
│   │   │   ├── ContentList.tsx   # 内容列表
│   │   │   └── StatsPanel.tsx    # 统计面板
│   │   └── lib/
│   │       └── api.ts            # API客户端
│   └── package.json
├── alembic/                      # 数据库迁移
├── tests/                        # 测试用例
├── pyproject.toml                # Python依赖配置
└── README.md                     # 本文件
```

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (生产) / SQLite (开发)

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/Mike4Ellis/nexus-zero.git
cd nexus-zero
```

2. **安装Python依赖**
```bash
pip install -e ".[dev]"
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 填入你的配置
```

4. **初始化数据库**
```bash
alembic upgrade head
```

5. **启动后端服务**
```bash
python -m src.api.main
# 或
uvicorn src.api.main:app --reload
```

6. **启动前端开发服务器**
```bash
cd web
npm install
npm run dev
```

访问 http://localhost:3000 查看Web界面

## 📡 API文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/stats` | GET | 获取统计数据 |
| `/api/briefs/latest` | GET | 获取最新简报 |
| `/api/briefs` | GET | 获取简报列表 |
| `/api/contents` | GET | 获取内容列表 |
| `/api/sources` | GET | 获取数据源列表 |
| `/health` | GET | 健康检查 |

## 🧪 运行测试

```bash
# Python测试
pytest

# 前端测试
cd web
npm test
```

## 📦 部署

### Docker部署 (TODO)

```bash
docker-compose up -d
```

### 手动部署

1. 使用Gunicorn运行后端：
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.api.main:app
```

2. 构建前端：
```bash
cd web
npm run build
```

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 后端语言 | Python 3.11+ |
| Web框架 | FastAPI |
| 数据库 | PostgreSQL / SQLite |
| ORM | SQLAlchemy 2.0 |
| 迁移 | Alembic |
| 调度 | APScheduler |
| 前端框架 | Next.js 14 |
| 样式 | Tailwind CSS |
| 类型检查 | mypy |
| 代码风格 | ruff |

## 📝 配置说明

### 环境变量

```env
# 数据库
DATABASE_URL=postgresql://user:pass@localhost/nexus_zero
# 或 SQLite: sqlite:///./nexus_zero.db

# X/Twitter API
X_BEARER_TOKEN=your_bearer_token

# Reddit API
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_secret

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# 邮件 (gog skill)
GOG_EMAIL_ENABLED=true
```

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 高性能Web框架
- [Next.js](https://nextjs.org/) - React全栈框架
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL工具包

---

*由 Gre (小魔怪Gremins) 🦎 协助开发*
