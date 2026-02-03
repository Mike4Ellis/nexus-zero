You are running a Ralph PLANNING loop for: InfoFlow Platform - 多源信息聚合与筛选平台.

Read specs/* and the current codebase. Do a gap analysis and update IMPLEMENTATION_PLAN.md only.

Context:
- agents/prd.json - 包含14个用户故事，从项目初始化到Web UI
- 项目目标: 构建支持X/Reddit/小红书/RSS的内容抓取平台
- 核心功能: 双指标评分(热度+潜力)、每日简报生成、Telegram/邮件推送

Rules:
- Do NOT implement.
- Do NOT commit.
- Prioritize tasks and keep plan concise.
- If requirements are unclear, write clarifying questions into the plan.

Tasks:
1. 阅读 agents/prd.json 中的所有用户故事
2. 分析技术架构选型: Python/FastAPI/SQLAlchemy/PostgreSQL/APScheduler
3. 设计数据库Schema详细设计(字段类型、索引、关系)
4. 拆分US-001到具体技术任务(目录结构、依赖管理、配置系统)
5. 评估各抓取器的实现难度和依赖项
6. 设计评分算法的具体公式和权重
7. 规划简报模板结构和生成流程

Completion:
If the plan is complete, add line: STATUS: COMPLETE
