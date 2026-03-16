# FinMate — AI 财务助理

面向客户/投资人演示的 AI 财务助理原型，覆盖银行对账、税务准备、财务报表、成本分摊四大模块。

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 19 + Vite + TypeScript + Ant Design 5 + ECharts + Zustand |
| 后端 | FastAPI + SQLAlchemy 2.0 async + SQLite (aiosqlite) |
| AI | Claude API (`claude-sonnet-4-6`) tool_use + SSE 流式输出 |

## 目录结构

```
FinMate/
├── backend/
│   ├── app/
│   │   ├── agent/          # AI agent：工具定义 + 多步推理循环
│   │   ├── api/            # FastAPI 路由
│   │   ├── mock/           # 种子数据（星辰科技 2024-01~03）
│   │   ├── models/         # SQLAlchemy ORM 模型
│   │   └── services/       # 业务逻辑层
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/     # AIAssistant、PeriodSelector、AmountCell
│       ├── pages/          # Dashboard、Reconciliation、Tax、Reports、CostAlloc
│       ├── services/api.ts # 后端 API 客户端（含 SSE streamChat）
│       ├── store/          # Zustand stores（period、chat）
│       └── types/          # TypeScript 类型定义
└── docs/
    └── superpowers/plans/  # 实施计划文档
```

## 快速启动

### 环境要求

- Python 3.11–3.13（不支持 3.14，pydantic-core/PyO3 限制）
- Node.js 18+

### 1. 配置环境变量

在 `FinMate/` 目录下创建 `.env` 文件：

```env
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

> AI 对话功能需要有效的 Anthropic API Key。其余功能（对账、税务、报表、成本分摊）不依赖 API Key。

### 2. 启动后端

```bash
cd FinMate

# 创建 venv（首次）
python3.13 -m venv venv

# 激活
source venv/bin/activate          # macOS/Linux
# venv\Scripts\activate           # Windows

# 安装依赖
pip install -r backend/requirements.txt

# 启动（端口 8000）
uvicorn backend.app.main:app --reload
```

首次启动时后端会**自动建表并导入 mock 数据**，无需手动操作。

日志示例：
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 3. 启动前端

```bash
cd FinMate/frontend
npm install
npm run dev
```

前端默认运行在 http://localhost:5173，API 请求通过 Vite proxy 转发至 `http://localhost:8000`。

## Mock 数据说明

种子数据模拟公司：**星辰科技有限公司**，期间 **2024-01 ~ 2024-03**。

| 数据集 | 数量 |
|--------|------|
| 会计科目 | 60 个（按小企业会计准则） |
| 银行流水 | ~144 笔（每月约 48 笔，正负双向） |
| 会计分录 | ~180 条（借贷平衡，三栏式） |
| 科目余额 | ~180 条（由分录聚合，非随机） |
| 成本中心 | 5 个 |
| 费用池 | 15 个 |
| 分摊规则 | 5 条 |
| 税务映射 | 6 条 |
| 报表模板 | 资产负债表 + 利润表 + 现金流量表共 51 行 |

数据通过 `backend/app/mock/seed.py` 的 `run_seed()` 函数生成，使用固定随机种子（`random.seed(42)`）保证可复现性。

### 重置数据库

```bash
# 删除数据库文件后重启后端即可重新 seed
rm FinMate/finmate.db
uvicorn backend.app.main:app --reload
```

## API 文档

后端启动后访问：

- Swagger UI：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc

## 主要 API 端点

| 模块 | 端点 |
|------|------|
| 仪表盘 | `GET /api/v1/dashboard/summary` |
| 银行对账 | `GET /api/v1/reconciliation/status` |
| 银行对账 | `GET /api/v1/reconciliation/transactions` |
| 银行对账 | `POST /api/v1/reconciliation/auto-match` |
| 税务 | `GET /api/v1/tax/estimate` |
| 税务 | `GET /api/v1/tax/filing` |
| 报表 | `GET /api/v1/reports/{report_type}` |
| 报表 | `GET /api/v1/reports/indicators` |
| 成本分摊 | `GET /api/v1/cost-alloc/results` |
| 成本分摊 | `POST /api/v1/cost-alloc/calculate` |
| AI 对话 | `POST /api/v1/ai-chat/stream`（SSE） |

## AI 对话说明

右侧面板为 AI 财务助理，切换菜单时自动切换 `module_context`，Agent 会按当前模块选取相关工具（共 13 个）进行多步推理（最多 5 轮 tool_use）。

SSE 事件格式：
```
data: {"type": "text", "content": "..."}\n\n
data: {"type": "tool_call", "tool": "query_bank_transactions", "input": {...}}\n\n
data: {"type": "tool_result", "tool": "...", "result": {...}}\n\n
data: {"type": "done"}\n\n
data: [DONE]\n\n
```
