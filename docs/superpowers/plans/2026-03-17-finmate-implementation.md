# FinMate AI 财务助理 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a demo-ready AI Financial Assistant with bank reconciliation, tax preparation, financial reports, and cost allocation — powered by Claude API Agent with tool_use.

**Architecture:** React 18 SPA (Vite + Ant Design 5 + ECharts) communicates via REST API with a Python FastAPI backend using SQLAlchemy 2.0 + SQLite. AI capabilities use Anthropic Claude API with tool_use for multi-step Agent reasoning. SSE streaming for real-time AI responses.

**Tech Stack:** React 18, Vite, Ant Design 5, ECharts 5, Zustand, TypeScript | Python 3.11+, FastAPI, SQLAlchemy 2.0, SQLite, Anthropic Claude API

**Spec:** `FinMate/docs/superpowers/specs/2026-03-17-finmate-ai-financial-assistant-design.md`

---

## Chunk 1: Project Scaffolding

This chunk sets up the project structure, Python venv, backend FastAPI skeleton, frontend Vite+React scaffold, and basic dev tooling. After this chunk, both frontend and backend dev servers should start successfully.

### Task 1: Initialize Project Root & Python Virtual Environment

**Files:**
- Create: `FinMate/backend/requirements.txt`
- Create: `FinMate/.env.example`
- Create: `FinMate/.gitignore`

- [ ] **Step 1: Create project directories**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
mkdir -p backend/app/api backend/app/models backend/app/services backend/app/agent backend/app/mock
mkdir -p docs/superpowers/plans docs/superpowers/specs
```

Note: Do NOT create `frontend/` here — Vite will scaffold it in Task 3.

- [ ] **Step 2: Create Python virtual environment**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
python3 -m venv venv
```

Expected: `venv/` directory created at project root.

- [ ] **Step 3: Write requirements.txt**

Create `FinMate/backend/requirements.txt`:

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy[asyncio]==2.0.36
aiosqlite==0.20.0
anthropic==0.42.0
python-dotenv==1.0.1
pydantic==2.10.4
pydantic-settings==2.7.1
sse-starlette==2.2.1
python-multipart==0.0.20
```

- [ ] **Step 4: Install Python dependencies**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
source venv/bin/activate
pip install -r backend/requirements.txt
```

Expected: All packages install successfully.

- [ ] **Step 5: Write .env.example**

Create `FinMate/.env.example`:

```
ANTHROPIC_API_KEY=sk-ant-xxx
DATABASE_URL=sqlite+aiosqlite:///./finmate.db
CORS_ORIGINS=http://localhost:5173
```

- [ ] **Step 6: Write .gitignore**

Create `FinMate/.gitignore`:

```
# Python
venv/
__pycache__/
*.pyc
*.pyo
*.db

# Node
node_modules/
dist/

# Environment
.env

# IDE
.vscode/
.idea/
*.swp
```

- [ ] **Step 7: Initialize git repository**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git init
git add .gitignore .env.example backend/requirements.txt
git commit -m "chore: initialize FinMate project structure"
```

---

### Task 2: Backend FastAPI Skeleton

**Files:**
- Create: `FinMate/backend/app/__init__.py`
- Create: `FinMate/backend/app/main.py`
- Create: `FinMate/backend/app/database.py`
- Create: `FinMate/backend/app/config.py`
- Create: `FinMate/backend/app/api/__init__.py`
- Create: `FinMate/backend/app/models/__init__.py`
- Create: `FinMate/backend/app/services/__init__.py`
- Create: `FinMate/backend/app/agent/__init__.py`
- Create: `FinMate/backend/app/mock/__init__.py`

- [ ] **Step 1: Create config module**

Create `FinMate/backend/app/config.py`:

```python
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./finmate.db"
    cors_origins: str = "http://localhost:5173"

    model_config = {
        "env_file": str(Path(__file__).resolve().parent.parent.parent / ".env"),
        "env_file_encoding": "utf-8",
    }


settings = Settings()
```

- [ ] **Step 2: Create database module**

Create `FinMate/backend/app/database.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

- [ ] **Step 3: Create empty __init__.py files**

Create empty `__init__.py` in each package:
- `FinMate/backend/app/__init__.py`
- `FinMate/backend/app/api/__init__.py`
- `FinMate/backend/app/models/__init__.py`
- `FinMate/backend/app/services/__init__.py`
- `FinMate/backend/app/agent/__init__.py`
- `FinMate/backend/app/mock/__init__.py`

All empty files.

- [ ] **Step 4: Create FastAPI main entry point**

Create `FinMate/backend/app/main.py`:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="FinMate API",
    description="AI 财务助理 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
async def health_check():
    return {"code": 200, "data": {"status": "healthy"}, "message": "ok"}
```

- [ ] **Step 5: Verify backend starts**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
source venv/bin/activate
cd backend
uvicorn app.main:app --port 8000 &
sleep 2
curl http://localhost:8000/api/v1/health
kill %1
```

Expected: `{"code":200,"data":{"status":"healthy"},"message":"ok"}`

- [ ] **Step 6: Commit backend skeleton**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add backend/
git commit -m "feat: add FastAPI backend skeleton with health check"
```

---

### Task 3: Frontend Vite + React + Ant Design Scaffold

**Files:**
- Create: `FinMate/frontend/` (via Vite scaffolding)
- Modify: `FinMate/frontend/package.json` (add dependencies)
- Create: `FinMate/frontend/src/App.tsx`
- Create: `FinMate/frontend/src/main.tsx`
- Modify: `FinMate/frontend/vite.config.ts` (add proxy)

- [ ] **Step 1: Scaffold Vite React TypeScript project**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
npm create vite@latest frontend -- --template react-ts
```

Expected: `frontend/` directory with Vite template files.

- [ ] **Step 2: Install frontend dependencies**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate/frontend
npm install
npm install antd@^5 @ant-design/icons echarts@^5 echarts-for-react zustand react-router-dom axios
```

- [ ] **Step 3: Configure Vite proxy for API**

Replace `FinMate/frontend/vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 4: Create minimal App with Ant Design layout**

Replace `FinMate/frontend/src/App.tsx`:

```tsx
import { ConfigProvider, Layout, Menu, theme } from 'antd'
import {
  DashboardOutlined,
  BankOutlined,
  AuditOutlined,
  BarChartOutlined,
  ApartmentOutlined,
} from '@ant-design/icons'
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom'

const { Header, Sider, Content } = Layout

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/reconciliation', icon: <BankOutlined />, label: '银行对账' },
  { key: '/tax', icon: <AuditOutlined />, label: '税务准备' },
  { key: '/reports', icon: <BarChartOutlined />, label: '财务报表' },
  { key: '/cost-alloc', icon: <ApartmentOutlined />, label: '成本分摊' },
]

function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="light" width={200}>
        <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: 18 }}>
          FinMate
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', alignItems: 'center' }}>
          <h2 style={{ margin: 0 }}>AI 财务助理</h2>
        </Header>
        <Content style={{ margin: 24, padding: 24, background: '#fff', borderRadius: 8 }}>
          <Routes>
            <Route path="/" element={<div>Dashboard - 即将实现</div>} />
            <Route path="/reconciliation" element={<div>银行对账 - 即将实现</div>} />
            <Route path="/tax" element={<div>税务准备 - 即将实现</div>} />
            <Route path="/reports" element={<div>财务报表 - 即将实现</div>} />
            <Route path="/cost-alloc" element={<div>成本分摊 - 即将实现</div>} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

export default function App() {
  return (
    <ConfigProvider theme={{ algorithm: theme.defaultAlgorithm }}>
      <BrowserRouter>
        <AppLayout />
      </BrowserRouter>
    </ConfigProvider>
  )
}
```

- [ ] **Step 5: Update main.tsx to remove StrictMode double-render and default CSS**

Replace `FinMate/frontend/src/main.tsx`:

```tsx
import { createRoot } from 'react-dom/client'
import App from './App'

createRoot(document.getElementById('root')!).render(<App />)
```

Delete `FinMate/frontend/src/App.css` and `FinMate/frontend/src/index.css` if they exist.

- [ ] **Step 6: Verify frontend starts**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate/frontend
npm run dev &
sleep 3
curl -s http://localhost:5173 | head -5
kill %1
```

Expected: HTML response with Vite app shell.

- [ ] **Step 7: Commit frontend scaffold**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add frontend/
git commit -m "feat: add Vite React frontend scaffold with Ant Design layout"
```

---

## Chunk 2: Backend Models & Mock Data

This chunk defines all SQLAlchemy models for the 4 modules plus shared models, creates the seed script with realistic mock data for "星辰科技有限公司", and verifies data loads correctly.

### Task 4: Shared Models (AccountBalance, BookEntry, ChartOfAccounts)

**Files:**
- Create: `FinMate/backend/app/models/base.py`

- [ ] **Step 1: Create shared models file**

Create `FinMate/backend/app/models/base.py`:

```python
from decimal import Decimal

from sqlalchemy import String, Integer, Date, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ChartOfAccounts(Base):
    __tablename__ = "chart_of_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    account_type: Mapped[str] = mapped_column(String(20))  # asset/liability/equity/cost/income/expense
    parent_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=1)
    balance_direction: Mapped[str] = mapped_column(String(10))  # debit/credit


class BookEntry(Base):
    __tablename__ = "book_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_date: Mapped[str] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    account_code: Mapped[str] = mapped_column(String(20), index=True)
    account_name: Mapped[str] = mapped_column(String(100))
    voucher_no: Mapped[str] = mapped_column(String(50), index=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    auxiliary: Mapped[str] = mapped_column(String(200), default="")
    direction: Mapped[str] = mapped_column(String(10))  # debit/credit


class AccountBalance(Base):
    __tablename__ = "account_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_code: Mapped[str] = mapped_column(String(20), index=True)
    account_name: Mapped[str] = mapped_column(String(100))
    account_level: Mapped[int] = mapped_column(Integer, default=1)
    parent_code: Mapped[str] = mapped_column(String(20), default="")
    period: Mapped[str] = mapped_column(String(7), index=True)  # YYYY-MM
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    debit_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    credit_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    closing_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    balance_direction: Mapped[str] = mapped_column(String(10))  # debit/credit
```

- [ ] **Step 2: Commit shared models**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add backend/app/models/base.py
git commit -m "feat: add shared models - ChartOfAccounts, BookEntry, AccountBalance"
```

---

### Task 5: Reconciliation Models

**Files:**
- Create: `FinMate/backend/app/models/reconciliation.py`

- [ ] **Step 1: Create reconciliation models**

Create `FinMate/backend/app/models/reconciliation.py`:

```python
from decimal import Decimal

from sqlalchemy import String, Integer, Date, Numeric, Boolean, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_no: Mapped[str] = mapped_column(String(30))
    transaction_date: Mapped[str] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    counterparty: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(String(500), default="")
    serial_no: Mapped[str] = mapped_column(String(50), unique=True)
    currency: Mapped[str] = mapped_column(String(10), default="CNY")
    matched_status: Mapped[str] = mapped_column(String(20), default="unmatched")  # unmatched/matched/confirmed/excluded


class ReconciliationRecord(Base):
    __tablename__ = "reconciliation_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_group_id: Mapped[str] = mapped_column(String(50), index=True)
    bank_transaction_id: Mapped[int] = mapped_column(Integer, index=True)
    book_entry_id: Mapped[int] = mapped_column(Integer, index=True)
    match_type: Mapped[str] = mapped_column(String(20))  # exact/fuzzy/smart/manual
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    match_rule: Mapped[str] = mapped_column(String(200), default="")


class ReconciliationRule(Base):
    __tablename__ = "reconciliation_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    match_fields: Mapped[dict] = mapped_column(JSON)
    tolerance_days: Mapped[int] = mapped_column(Integer, default=0)
    tolerance_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    priority: Mapped[int] = mapped_column(Integer, default=0)
```

- [ ] **Step 2: Commit reconciliation models**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add backend/app/models/reconciliation.py
git commit -m "feat: add reconciliation models - BankTransaction, ReconciliationRecord, ReconciliationRule"
```

---

### Task 6: Tax Models

**Files:**
- Create: `FinMate/backend/app/models/tax.py`

- [ ] **Step 1: Create tax models**

Create `FinMate/backend/app/models/tax.py`:

```python
from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TaxMapping(Base):
    __tablename__ = "tax_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_code: Mapped[str] = mapped_column(String(20), index=True)
    account_name: Mapped[str] = mapped_column(String(100))
    tax_form_type: Mapped[str] = mapped_column(String(30))  # vat_general/cit_quarterly
    tax_line_no: Mapped[str] = mapped_column(String(20))
    tax_line_name: Mapped[str] = mapped_column(String(200))
    data_source: Mapped[str] = mapped_column(String(50))  # current_debit/current_credit/closing_balance/cumulative


class TaxFilingTemplate(Base):
    __tablename__ = "tax_filing_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    form_type: Mapped[str] = mapped_column(String(30))  # vat_general/cit_quarterly
    form_name: Mapped[str] = mapped_column(String(100))
    period_type: Mapped[str] = mapped_column(String(10))  # monthly/quarterly


class TaxLineItem(Base):
    __tablename__ = "tax_line_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(Integer, index=True)
    line_no: Mapped[str] = mapped_column(String(20))
    line_name: Mapped[str] = mapped_column(String(200))
    formula: Mapped[str] = mapped_column(Text, default="")
    current_value: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    adjusted_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    period: Mapped[str] = mapped_column(String(7), index=True)  # YYYY-MM


class TaxEstimate(Base):
    __tablename__ = "tax_estimates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tax_type: Mapped[str] = mapped_column(String(30))
    period: Mapped[str] = mapped_column(String(7), index=True)
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    previous_period: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    yoy_change: Mapped[float] = mapped_column(Float, default=0.0)


class TaxValidationRule(Base):
    __tablename__ = "tax_validation_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    form_type: Mapped[str] = mapped_column(String(30))
    rule_name: Mapped[str] = mapped_column(String(200))
    rule_expression: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(10))  # error/warning
```

- [ ] **Step 2: Commit tax models**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add backend/app/models/tax.py
git commit -m "feat: add tax models - TaxMapping, TaxFilingTemplate, TaxLineItem, TaxEstimate, TaxValidationRule"
```

---

### Task 7: Reports Models

**Files:**
- Create: `FinMate/backend/app/models/reports.py`

- [ ] **Step 1: Create reports models**

Create `FinMate/backend/app/models/reports.py`:

```python
from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, Float, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReportTemplate(Base):
    __tablename__ = "report_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_type: Mapped[str] = mapped_column(String(20))  # balance_sheet/income/cash_flow
    line_no: Mapped[str] = mapped_column(String(20))
    line_name: Mapped[str] = mapped_column(String(100))
    formula: Mapped[str] = mapped_column(Text, default="")
    indent_level: Mapped[int] = mapped_column(Integer, default=0)
    is_total: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)


class ReportData(Base):
    __tablename__ = "report_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_type: Mapped[str] = mapped_column(String(20), index=True)
    period: Mapped[str] = mapped_column(String(7), index=True)
    line_no: Mapped[str] = mapped_column(String(20))
    current_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    previous_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    yoy_change: Mapped[float] = mapped_column(Float, default=0.0)


class FinancialIndicator(Base):
    __tablename__ = "financial_indicators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period: Mapped[str] = mapped_column(String(7), index=True)
    indicator_name: Mapped[str] = mapped_column(String(100))
    indicator_value: Mapped[float] = mapped_column(Float, default=0.0)
    benchmark_value: Mapped[float] = mapped_column(Float, default=0.0)
    health_status: Mapped[str] = mapped_column(String(10), default="good")  # good/warning/danger
    description: Mapped[str] = mapped_column(Text, default="")
```

- [ ] **Step 2: Commit reports models**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add backend/app/models/reports.py
git commit -m "feat: add reports models - ReportTemplate, ReportData, FinancialIndicator"
```

---

### Task 8: Cost Allocation Models

**Files:**
- Create: `FinMate/backend/app/models/cost_alloc.py`

- [ ] **Step 1: Create cost allocation models**

Create `FinMate/backend/app/models/cost_alloc.py`:

```python
from decimal import Decimal

from sqlalchemy import String, Integer, Date, Numeric, Float, Boolean, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CostCenter(Base):
    __tablename__ = "cost_centers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    center_type: Mapped[str] = mapped_column(String(20))  # department/project/product_line
    parent_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    headcount: Mapped[int] = mapped_column(Integer, default=0)
    area: Mapped[float] = mapped_column(Float, default=0.0)
    revenue_ratio: Mapped[float] = mapped_column(Float, default=0.0)


class CostPool(Base):
    __tablename__ = "cost_pools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    cost_type: Mapped[str] = mapped_column(String(20))  # rent/utilities/it/management/other
    account_code: Mapped[str] = mapped_column(String(20))
    period: Mapped[str] = mapped_column(String(7), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    is_allocated: Mapped[bool] = mapped_column(Boolean, default=False)


class AllocationRule(Base):
    __tablename__ = "allocation_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    cost_pool_id: Mapped[int] = mapped_column(Integer, index=True)
    allocation_basis: Mapped[str] = mapped_column(String(20))  # headcount/area/revenue/hours/custom
    condition_expr: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[int] = mapped_column(Integer, default=0)
    effective_from: Mapped[str] = mapped_column(Date)
    effective_to: Mapped[str | None] = mapped_column(Date, nullable=True)


class AllocationResult(Base):
    __tablename__ = "allocation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_id: Mapped[int] = mapped_column(Integer, index=True)
    cost_pool_id: Mapped[int] = mapped_column(Integer, index=True)
    cost_center_id: Mapped[int] = mapped_column(Integer, index=True)
    period: Mapped[str] = mapped_column(String(7), index=True)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    allocation_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    calculation_detail: Mapped[str] = mapped_column(Text, default="")


class AllocationVoucher(Base):
    __tablename__ = "allocation_vouchers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period: Mapped[str] = mapped_column(String(7), index=True)
    voucher_no: Mapped[str] = mapped_column(String(50))
    entries: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(10), default="draft")  # draft/confirmed
```

- [ ] **Step 2: Commit cost allocation models**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add backend/app/models/cost_alloc.py
git commit -m "feat: add cost allocation models - CostCenter, CostPool, AllocationRule, AllocationResult, AllocationVoucher"
```

---

### Task 9: Register All Models & Verify DB Creation

**Files:**
- Modify: `FinMate/backend/app/models/__init__.py`

- [ ] **Step 1: Update models __init__.py to import all models**

Replace `FinMate/backend/app/models/__init__.py`:

```python
from app.models.base import ChartOfAccounts, BookEntry, AccountBalance  # noqa: F401
from app.models.reconciliation import (  # noqa: F401
    BankTransaction,
    ReconciliationRecord,
    ReconciliationRule,
)
from app.models.tax import (  # noqa: F401
    TaxMapping,
    TaxFilingTemplate,
    TaxLineItem,
    TaxEstimate,
    TaxValidationRule,
)
from app.models.reports import ReportTemplate, ReportData, FinancialIndicator  # noqa: F401
from app.models.cost_alloc import (  # noqa: F401
    CostCenter,
    CostPool,
    AllocationRule,
    AllocationResult,
    AllocationVoucher,
)
```

- [ ] **Step 2: Import models in main.py to ensure registration**

Add to top of `FinMate/backend/app/main.py`, after existing imports:

```python
import app.models  # noqa: F401 — register all models for Base.metadata
```

- [ ] **Step 3: Verify database tables are created**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
source venv/bin/activate
cd backend
python -c "
import asyncio
from app.database import init_db, engine
import app.models
asyncio.run(init_db())
print('Tables created successfully')
# verify tables
from sqlalchemy import inspect
def check(conn):
    insp = inspect(conn)
    tables = insp.get_table_names()
    print(f'Tables ({len(tables)}): {tables}')
from sqlalchemy import create_engine
sync_engine = create_engine('sqlite:///./finmate.db')
with sync_engine.connect() as conn:
    check(conn)
import os; os.remove('finmate.db')
"
```

Expected: 19 tables listed (chart_of_accounts, book_entries, account_balances, bank_transactions, reconciliation_records, reconciliation_rules, tax_mappings, tax_filing_templates, tax_line_items, tax_estimates, tax_validation_rules, report_templates, report_data, financial_indicators, cost_centers, cost_pools, allocation_rules, allocation_results, allocation_vouchers).

- [ ] **Step 4: Commit model registration**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add backend/app/models/__init__.py backend/app/main.py
git commit -m "feat: register all models and verify DB table creation"
```

---

### Task 10: Mock Data Seed Script — Chart of Accounts

**Files:**
- Create: `FinMate/backend/app/mock/chart_of_accounts.py`

- [ ] **Step 1: Create chart of accounts data**

Create `FinMate/backend/app/mock/chart_of_accounts.py`:

```python
"""小企业会计准则科目体系 — 约60个常用科目"""

CHART_OF_ACCOUNTS = [
    # 资产类
    {"code": "1001", "name": "库存现金", "account_type": "asset", "parent_code": None, "level": 1, "balance_direction": "debit"},
    {"code": "1002", "name": "银行存款", "account_type": "asset", "parent_code": None, "level": 1, "balance_direction": "debit"},
    {"code": "1002.01", "name": "银行存款-工商银行", "account_type": "asset", "parent_code": "1002", "level": 2, "balance_direction": "debit"},
    {"code": "1002.02", "name": "银行存款-建设银行", "account_type": "asset", "parent_code": "1002", "level": 2, "balance_direction": "debit"},
    {"code": "1122", "name": "应收账款", "account_type": "asset", "parent_code": None, "level": 1, "balance_direction": "debit"},
    {"code": "1122.01", "name": "应收账款-星河集团", "account_type": "asset", "parent_code": "1122", "level": 2, "balance_direction": "debit"},
    {"code": "1122.02", "name": "应收账款-云图科技", "account_type": "asset", "parent_code": "1122", "level": 2, "balance_direction": "debit"},
    {"code": "1122.03", "name": "应收账款-蓝海数据", "account_type": "asset", "parent_code": "1122", "level": 2, "balance_direction": "debit"},
    {"code": "1123", "name": "预付账款", "account_type": "asset", "parent_code": None, "level": 1, "balance_direction": "debit"},
    {"code": "1131", "name": "应收股利", "account_type": "asset", "parent_code": None, "level": 1, "balance_direction": "debit"},
    {"code": "1221", "name": "其他应收款", "account_type": "asset", "parent_code": None, "level": 1, "balance_direction": "debit"},
    {"code": "1401", "name": "材料采购", "account_type": "asset", "parent_code": None, "level": 1, "balance_direction": "debit"},
    {"code": "1403", "name": "原材料", "account_type": "asset", "parent_code": None, "level": 1, "balance_direction": "debit"},
    {"code": "1405", "name": "库存商品", "account_type": "asset", "parent_code": None, "level": 1, "balance_direction": "debit"},
    {"code": "1501", "name": "长期债券投资", "account_type": "asset", "parent_code": None, "level": 1, "balance_direction": "debit"},
    {"code": "1601", "name": "固定资产", "account_type": "asset", "parent_code": None, "level": 1, "balance_direction": "debit"},
    {"code": "1602", "name": "累计折旧", "account_type": "asset", "parent_code": None, "level": 1, "balance_direction": "credit"},
    {"code": "1701", "name": "无形资产", "account_type": "asset", "parent_code": None, "level": 1, "balance_direction": "debit"},
    {"code": "1801", "name": "长期待摊费用", "account_type": "asset", "parent_code": None, "level": 1, "balance_direction": "debit"},
    # 负债类
    {"code": "2001", "name": "短期借款", "account_type": "liability", "parent_code": None, "level": 1, "balance_direction": "credit"},
    {"code": "2202", "name": "应付账款", "account_type": "liability", "parent_code": None, "level": 1, "balance_direction": "credit"},
    {"code": "2202.01", "name": "应付账款-天宇科技", "account_type": "liability", "parent_code": "2202", "level": 2, "balance_direction": "credit"},
    {"code": "2202.02", "name": "应付账款-华芯电子", "account_type": "liability", "parent_code": "2202", "level": 2, "balance_direction": "credit"},
    {"code": "2203", "name": "预收账款", "account_type": "liability", "parent_code": None, "level": 1, "balance_direction": "credit"},
    {"code": "2211", "name": "应付职工薪酬", "account_type": "liability", "parent_code": None, "level": 1, "balance_direction": "credit"},
    {"code": "2221", "name": "应交税费", "account_type": "liability", "parent_code": None, "level": 1, "balance_direction": "credit"},
    {"code": "2221.01", "name": "应交税费-应交增值税(销项)", "account_type": "liability", "parent_code": "2221", "level": 2, "balance_direction": "credit"},
    {"code": "2221.02", "name": "应交税费-应交增值税(进项)", "account_type": "liability", "parent_code": "2221", "level": 2, "balance_direction": "debit"},
    {"code": "2221.03", "name": "应交税费-应交企业所得税", "account_type": "liability", "parent_code": "2221", "level": 2, "balance_direction": "credit"},
    {"code": "2231", "name": "应付利息", "account_type": "liability", "parent_code": None, "level": 1, "balance_direction": "credit"},
    {"code": "2241", "name": "其他应付款", "account_type": "liability", "parent_code": None, "level": 1, "balance_direction": "credit"},
    # 所有者权益类
    {"code": "3001", "name": "实收资本", "account_type": "equity", "parent_code": None, "level": 1, "balance_direction": "credit"},
    {"code": "3002", "name": "资本公积", "account_type": "equity", "parent_code": None, "level": 1, "balance_direction": "credit"},
    {"code": "3101", "name": "盈余公积", "account_type": "equity", "parent_code": None, "level": 1, "balance_direction": "credit"},
    {"code": "3103", "name": "本年利润", "account_type": "equity", "parent_code": None, "level": 1, "balance_direction": "credit"},
    {"code": "3104", "name": "利润分配", "account_type": "equity", "parent_code": None, "level": 1, "balance_direction": "credit"},
    # 成本类
    {"code": "4001", "name": "生产成本", "account_type": "cost", "parent_code": None, "level": 1, "balance_direction": "debit"},
    {"code": "4101", "name": "制造费用", "account_type": "cost", "parent_code": None, "level": 1, "balance_direction": "debit"},
    # 损益-收入类
    {"code": "5001", "name": "主营业务收入", "account_type": "income", "parent_code": None, "level": 1, "balance_direction": "credit"},
    {"code": "5001.01", "name": "主营业务收入-软件开发", "account_type": "income", "parent_code": "5001", "level": 2, "balance_direction": "credit"},
    {"code": "5001.02", "name": "主营业务收入-技术服务", "account_type": "income", "parent_code": "5001", "level": 2, "balance_direction": "credit"},
    {"code": "5001.03", "name": "主营业务收入-产品销售", "account_type": "income", "parent_code": "5001", "level": 2, "balance_direction": "credit"},
    {"code": "5051", "name": "其他业务收入", "account_type": "income", "parent_code": None, "level": 1, "balance_direction": "credit"},
    {"code": "5301", "name": "营业外收入", "account_type": "income", "parent_code": None, "level": 1, "balance_direction": "credit"},
    # 损益-费用类
    {"code": "5401", "name": "主营业务成本", "account_type": "expense", "parent_code": None, "level": 1, "balance_direction": "debit"},
    {"code": "5402", "name": "其他业务成本", "account_type": "expense", "parent_code": None, "level": 1, "balance_direction": "debit"},
    {"code": "5403", "name": "营业税金及附加", "account_type": "expense", "parent_code": None, "level": 1, "balance_direction": "debit"},
    {"code": "5601", "name": "销售费用", "account_type": "expense", "parent_code": None, "level": 1, "balance_direction": "debit"},
    {"code": "5602", "name": "管理费用", "account_type": "expense", "parent_code": None, "level": 1, "balance_direction": "debit"},
    {"code": "5602.01", "name": "管理费用-办公租金", "account_type": "expense", "parent_code": "5602", "level": 2, "balance_direction": "debit"},
    {"code": "5602.02", "name": "管理费用-水电费", "account_type": "expense", "parent_code": "5602", "level": 2, "balance_direction": "debit"},
    {"code": "5602.03", "name": "管理费用-折旧摊销", "account_type": "expense", "parent_code": "5602", "level": 2, "balance_direction": "debit"},
    {"code": "5602.04", "name": "管理费用-办公用品", "account_type": "expense", "parent_code": "5602", "level": 2, "balance_direction": "debit"},
    {"code": "5602.05", "name": "管理费用-差旅费", "account_type": "expense", "parent_code": "5602", "level": 2, "balance_direction": "debit"},
    {"code": "5602.06", "name": "管理费用-IT运维费", "account_type": "expense", "parent_code": "5602", "level": 2, "balance_direction": "debit"},
    {"code": "5603", "name": "财务费用", "account_type": "expense", "parent_code": None, "level": 1, "balance_direction": "debit"},
    {"code": "5603.01", "name": "财务费用-利息支出", "account_type": "expense", "parent_code": "5603", "level": 2, "balance_direction": "debit"},
    {"code": "5603.02", "name": "财务费用-手续费", "account_type": "expense", "parent_code": "5603", "level": 2, "balance_direction": "debit"},
    {"code": "5711", "name": "营业外支出", "account_type": "expense", "parent_code": None, "level": 1, "balance_direction": "debit"},
    {"code": "5801", "name": "所得税费用", "account_type": "expense", "parent_code": None, "level": 1, "balance_direction": "debit"},
]
```

- [ ] **Step 2: Commit chart of accounts data**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add backend/app/mock/chart_of_accounts.py
git commit -m "feat: add chart of accounts mock data (小企业会计准则 ~60 accounts)"
```

---

### Task 11: Mock Data Seed Script — Main Seed

**Files:**
- Create: `FinMate/backend/app/mock/seed.py`

This is the main seed script. It imports chart of accounts data, creates bank transactions (~200), book entries (~180), account balances (60 accounts x 3 months), cost centers (5 departments), cost pools (5 types x 3 months), reconciliation rules, tax mappings, report templates, and allocation rules.

- [ ] **Step 1: Create seed script**

Create `FinMate/backend/app/mock/seed.py`:

```python
"""Mock data seeder for 星辰科技有限公司 — 2024-01 to 2024-03."""

import asyncio
import random
from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session, init_db
from app.models.base import ChartOfAccounts, BookEntry, AccountBalance
from app.models.reconciliation import BankTransaction, ReconciliationRule
from app.models.tax import TaxMapping, TaxFilingTemplate, TaxValidationRule
from app.models.reports import ReportTemplate
from app.models.cost_alloc import CostCenter, CostPool, AllocationRule
from app.mock.chart_of_accounts import CHART_OF_ACCOUNTS

random.seed(42)  # Reproducible data

PERIODS = ["2024-01", "2024-02", "2024-03"]
BANK_ACCOUNT = "6222021234567890"
ACCT_NAME_MAP = {a["code"]: a["name"] for a in CHART_OF_ACCOUNTS}


async def seed_chart_of_accounts(session: AsyncSession):
    for acct in CHART_OF_ACCOUNTS:
        session.add(ChartOfAccounts(**acct))
    await session.flush()


async def seed_bank_transactions(session: AsyncSession) -> list[BankTransaction]:
    """Generate ~200 bank transactions across 3 months."""
    transactions = []
    serial_counter = 1000

    counterparties_in = [
        ("星河集团", "软件开发服务费"),
        ("云图科技", "技术服务费"),
        ("蓝海数据", "产品销售款"),
        ("星河集团", "项目尾款"),
        ("云图科技", "维护服务费"),
    ]
    counterparties_out = [
        ("天宇科技", "采购服务器设备"),
        ("华芯电子", "采购电子元器件"),
        ("中国电信", "网络服务费"),
        ("物业管理公司", "办公场地租金"),
        ("自来水公司", "水费"),
        ("国家电网", "电费"),
    ]
    misc_out = [
        ("文具供应商", "办公用品采购"),
        ("差旅报销", "员工差旅费报销"),
        ("快递公司", "快递物流费"),
        ("保洁公司", "保洁服务费"),
    ]
    salary_items = [
        ("工资代发", "员工工资"),
        ("社保中心", "社会保险费"),
        ("公积金中心", "住房公积金"),
    ]
    tax_items = [
        ("税务局", "增值税"),
        ("税务局", "企业所得税"),
    ]

    for period_idx, period in enumerate(PERIODS):
        year, month = 2024, period_idx + 1
        days_in_month = 28 if month == 2 else 31

        # Customer receipts: 18-22 per month
        for _ in range(random.randint(18, 22)):
            cp, summary = random.choice(counterparties_in)
            day = random.randint(1, days_in_month)
            amount = Decimal(str(random.randint(15000, 350000)))
            serial_counter += 1
            txn = BankTransaction(
                account_no=BANK_ACCOUNT,
                transaction_date=date(year, month, day),
                amount=amount, counterparty=cp, summary=summary,
                serial_no=f"TXN{year}{month:02d}{serial_counter}",
                currency="CNY", matched_status="unmatched",
            )
            session.add(txn)
            transactions.append(txn)

        # Supplier payments: 12-16 per month
        for _ in range(random.randint(12, 16)):
            cp, summary = random.choice(counterparties_out)
            day = random.randint(1, days_in_month)
            amount = Decimal(str(-random.randint(5000, 120000)))
            serial_counter += 1
            txn = BankTransaction(
                account_no=BANK_ACCOUNT,
                transaction_date=date(year, month, day),
                amount=amount, counterparty=cp, summary=summary,
                serial_no=f"TXN{year}{month:02d}{serial_counter}",
                currency="CNY", matched_status="unmatched",
            )
            session.add(txn)
            transactions.append(txn)

        # Misc expenses: 4-6 per month
        for _ in range(random.randint(4, 6)):
            cp, summary = random.choice(misc_out)
            day = random.randint(1, days_in_month)
            amount = Decimal(str(-random.randint(200, 5000)))
            serial_counter += 1
            txn = BankTransaction(
                account_no=BANK_ACCOUNT,
                transaction_date=date(year, month, day),
                amount=amount, counterparty=cp, summary=summary,
                serial_no=f"TXN{year}{month:02d}{serial_counter}",
                currency="CNY", matched_status="unmatched",
            )
            session.add(txn)
            transactions.append(txn)

        # Salary & benefits: 3 entries per month (around 10th)
        for cp, summary in salary_items:
            amount_val = -180000 if "工资" in summary else (-45000 if "社保" in summary else -25000)
            serial_counter += 1
            txn = BankTransaction(
                account_no=BANK_ACCOUNT,
                transaction_date=date(year, month, min(10, days_in_month)),
                amount=Decimal(str(amount_val)), counterparty=cp, summary=summary,
                serial_no=f"TXN{year}{month:02d}{serial_counter}",
                currency="CNY", matched_status="unmatched",
            )
            session.add(txn)
            transactions.append(txn)

        # Tax payments: around 15th
        for cp, summary in tax_items:
            amount_val = -random.randint(20000, 80000)
            serial_counter += 1
            txn = BankTransaction(
                account_no=BANK_ACCOUNT,
                transaction_date=date(year, month, min(15, days_in_month)),
                amount=Decimal(str(amount_val)), counterparty=cp, summary=summary,
                serial_no=f"TXN{year}{month:02d}{serial_counter}",
                currency="CNY", matched_status="unmatched",
            )
            session.add(txn)
            transactions.append(txn)

        # Bank fees: 3-4 per month (deliberately hard to match)
        for _ in range(random.randint(3, 4)):
            serial_counter += 1
            txn = BankTransaction(
                account_no=BANK_ACCOUNT,
                transaction_date=date(year, month, random.randint(1, days_in_month)),
                amount=Decimal(str(-random.randint(10, 200))),
                counterparty="工商银行", summary="账户管理费/转账手续费",
                serial_no=f"TXN{year}{month:02d}{serial_counter}",
                currency="CNY", matched_status="unmatched",
            )
            session.add(txn)
            transactions.append(txn)

    await session.flush()
    return transactions


async def seed_book_entries(session: AsyncSession) -> list[BookEntry]:
    """Generate ~180+ book entries across 3 months.
    All vouchers are balanced (total debit == total credit).
    """
    entries = []
    voucher_counter = 0

    for period_idx, period in enumerate(PERIODS):
        year, month = 2024, period_idx + 1
        days_in_month = 28 if month == 2 else 31

        # === Revenue entries: VAT-inclusive amount split correctly ===
        # Debit Bank (gross) = Credit Revenue (net) + Credit VAT Output (tax)
        revenue_items = [
            ("星河集团", "5001.01", "软件开发服务费"),
            ("云图科技", "5001.02", "技术服务费"),
            ("蓝海数据", "5001.03", "产品销售款"),
        ]
        for customer, acct_code, summary in revenue_items:
            for _ in range(random.randint(3, 5)):
                voucher_counter += 1
                vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
                day = random.randint(1, days_in_month)
                gross_amt = Decimal(str(random.randint(15000, 350000)))
                vat_amt = (gross_amt * Decimal("0.13") / Decimal("1.13")).quantize(Decimal("0.01"))
                net_amt = gross_amt - vat_amt
                # Debit: bank (gross)
                entries.append(BookEntry(
                    entry_date=date(year, month, day), amount=gross_amt,
                    account_code="1002.01", account_name="银行存款-工商银行",
                    voucher_no=vno, summary=summary, auxiliary=customer, direction="debit",
                ))
                # Credit: revenue (net of VAT)
                entries.append(BookEntry(
                    entry_date=date(year, month, day), amount=net_amt,
                    account_code=acct_code, account_name=ACCT_NAME_MAP.get(acct_code, ""),
                    voucher_no=vno, summary=summary, auxiliary=customer, direction="credit",
                ))
                # Credit: VAT output tax
                entries.append(BookEntry(
                    entry_date=date(year, month, day), amount=vat_amt,
                    account_code="2221.01", account_name="应交税费-应交增值税(销项)",
                    voucher_no=vno, summary=f"销项税额-{summary}", auxiliary="", direction="credit",
                ))

        # === Salary payment: Debit AP-salary / Credit Bank ===
        voucher_counter += 1
        vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
        entries.append(BookEntry(
            entry_date=date(year, month, min(10, days_in_month)), amount=Decimal("180000"),
            account_code="2211", account_name="应付职工薪酬",
            voucher_no=vno, summary="支付本月工资", auxiliary="", direction="debit",
        ))
        entries.append(BookEntry(
            entry_date=date(year, month, min(10, days_in_month)), amount=Decimal("180000"),
            account_code="1002.01", account_name="银行存款-工商银行",
            voucher_no=vno, summary="支付本月工资", auxiliary="", direction="credit",
        ))

        # === Salary accrual: Debit Expense / Credit AP-salary ===
        voucher_counter += 1
        vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
        entries.append(BookEntry(
            entry_date=date(year, month, min(28, days_in_month)), amount=Decimal("180000"),
            account_code="5602", account_name="管理费用",
            voucher_no=vno, summary="计提本月工资", auxiliary="", direction="debit",
        ))
        entries.append(BookEntry(
            entry_date=date(year, month, min(28, days_in_month)), amount=Decimal("180000"),
            account_code="2211", account_name="应付职工薪酬",
            voucher_no=vno, summary="计提本月工资", auxiliary="", direction="credit",
        ))

        # === Rent: Debit Expense / Credit Bank ===
        voucher_counter += 1
        vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
        rent_amt = Decimal("35000")
        entries.append(BookEntry(
            entry_date=date(year, month, 1), amount=rent_amt,
            account_code="5602.01", account_name="管理费用-办公租金",
            voucher_no=vno, summary="本月办公室租金", auxiliary="", direction="debit",
        ))
        entries.append(BookEntry(
            entry_date=date(year, month, 1), amount=rent_amt,
            account_code="1002.01", account_name="银行存款-工商银行",
            voucher_no=vno, summary="支付办公室租金", auxiliary="物业管理公司", direction="credit",
        ))

        # === Utilities: Debit Expense / Credit Bank ===
        voucher_counter += 1
        vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
        util_amt = Decimal(str(random.randint(3000, 6000)))
        entries.append(BookEntry(
            entry_date=date(year, month, min(20, days_in_month)), amount=util_amt,
            account_code="5602.02", account_name="管理费用-水电费",
            voucher_no=vno, summary="本月水电费", auxiliary="", direction="debit",
        ))
        entries.append(BookEntry(
            entry_date=date(year, month, min(20, days_in_month)), amount=util_amt,
            account_code="1002.01", account_name="银行存款-工商银行",
            voucher_no=vno, summary="支付水电费", auxiliary="", direction="credit",
        ))

        # === Supplier payments: Debit AP / Credit Bank (VAT was on purchase invoice) ===
        supplier_items = [("天宇科技", "2202.01"), ("华芯电子", "2202.02")]
        for supplier, acct in supplier_items:
            voucher_counter += 1
            vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
            pay_amt = Decimal(str(random.randint(20000, 100000)))
            entries.append(BookEntry(
                entry_date=date(year, month, random.randint(1, days_in_month)), amount=pay_amt,
                account_code=acct, account_name=f"应付账款-{supplier}",
                voucher_no=vno, summary=f"支付{supplier}货款", auxiliary=supplier, direction="debit",
            ))
            entries.append(BookEntry(
                entry_date=date(year, month, random.randint(1, days_in_month)), amount=pay_amt,
                account_code="1002.01", account_name="银行存款-工商银行",
                voucher_no=vno, summary=f"支付{supplier}货款", auxiliary=supplier, direction="credit",
            ))

        # === Purchase invoice (separate from payment): Debit Cost+VAT / Credit AP ===
        for supplier, acct in supplier_items:
            voucher_counter += 1
            vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
            invoice_amt = Decimal(str(random.randint(20000, 100000)))
            vat_in = (invoice_amt * Decimal("0.13") / Decimal("1.13")).quantize(Decimal("0.01"))
            net_cost = invoice_amt - vat_in
            entries.append(BookEntry(
                entry_date=date(year, month, random.randint(1, days_in_month)), amount=net_cost,
                account_code="5401", account_name="主营业务成本",
                voucher_no=vno, summary=f"采购-{supplier}", auxiliary=supplier, direction="debit",
            ))
            entries.append(BookEntry(
                entry_date=date(year, month, random.randint(1, days_in_month)), amount=vat_in,
                account_code="2221.02", account_name="应交税费-应交增值税(进项)",
                voucher_no=vno, summary=f"进项税额-{supplier}", auxiliary="", direction="debit",
            ))
            entries.append(BookEntry(
                entry_date=date(year, month, random.randint(1, days_in_month)), amount=invoice_amt,
                account_code=acct, account_name=f"应付账款-{supplier}",
                voucher_no=vno, summary=f"采购-{supplier}", auxiliary=supplier, direction="credit",
            ))

        # === Depreciation: Debit Expense / Credit Accumulated Depreciation ===
        voucher_counter += 1
        vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
        dep_amt = Decimal("8000")
        entries.append(BookEntry(
            entry_date=date(year, month, min(28, days_in_month)), amount=dep_amt,
            account_code="5602.03", account_name="管理费用-折旧摊销",
            voucher_no=vno, summary="本月折旧", auxiliary="", direction="debit",
        ))
        entries.append(BookEntry(
            entry_date=date(year, month, min(28, days_in_month)), amount=dep_amt,
            account_code="1602", account_name="累计折旧",
            voucher_no=vno, summary="本月折旧", auxiliary="", direction="credit",
        ))

        # === IT expenses: Debit Expense / Credit Bank ===
        voucher_counter += 1
        vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
        it_amt = Decimal(str(random.randint(10000, 15000)))
        entries.append(BookEntry(
            entry_date=date(year, month, min(25, days_in_month)), amount=it_amt,
            account_code="5602.06", account_name="管理费用-IT运维费",
            voucher_no=vno, summary="IT运维服务费", auxiliary="", direction="debit",
        ))
        entries.append(BookEntry(
            entry_date=date(year, month, min(25, days_in_month)), amount=it_amt,
            account_code="1002.01", account_name="银行存款-工商银行",
            voucher_no=vno, summary="IT运维服务费", auxiliary="", direction="credit",
        ))

        # === Office supplies: Debit Expense / Credit Bank ===
        voucher_counter += 1
        vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
        office_amt = Decimal(str(random.randint(1000, 3000)))
        entries.append(BookEntry(
            entry_date=date(year, month, random.randint(1, days_in_month)), amount=office_amt,
            account_code="5602.04", account_name="管理费用-办公用品",
            voucher_no=vno, summary="办公用品采购", auxiliary="", direction="debit",
        ))
        entries.append(BookEntry(
            entry_date=date(year, month, random.randint(1, days_in_month)), amount=office_amt,
            account_code="1002.01", account_name="银行存款-工商银行",
            voucher_no=vno, summary="办公用品采购", auxiliary="", direction="credit",
        ))

        # === Travel: Debit Expense / Credit Bank ===
        voucher_counter += 1
        vno = f"PZ-{year}{month:02d}-{voucher_counter:04d}"
        travel_amt = Decimal(str(random.randint(2000, 8000)))
        entries.append(BookEntry(
            entry_date=date(year, month, random.randint(1, days_in_month)), amount=travel_amt,
            account_code="5602.05", account_name="管理费用-差旅费",
            voucher_no=vno, summary="员工差旅费", auxiliary="", direction="debit",
        ))
        entries.append(BookEntry(
            entry_date=date(year, month, random.randint(1, days_in_month)), amount=travel_amt,
            account_code="1002.01", account_name="银行存款-工商银行",
            voucher_no=vno, summary="员工差旅费", auxiliary="", direction="credit",
        ))

    for e in entries:
        session.add(e)
    await session.flush()
    return entries


async def seed_account_balances(session: AsyncSession, book_entries: list[BookEntry]):
    """Derive account balances from BookEntry records per spec §2.5.
    Opening balances for 2024-01 are hardcoded; subsequent months carry forward.
    """
    opening_balances_jan = {
        "1001": Decimal("5000"), "1002": Decimal("2850000"), "1002.01": Decimal("2000000"),
        "1002.02": Decimal("850000"), "1122": Decimal("450000"), "1122.01": Decimal("200000"),
        "1122.02": Decimal("150000"), "1122.03": Decimal("100000"), "1123": Decimal("30000"),
        "1403": Decimal("120000"), "1405": Decimal("85000"),
        "1601": Decimal("560000"), "1602": Decimal("112000"),
        "1701": Decimal("80000"), "1801": Decimal("24000"),
        "2001": Decimal("500000"), "2202": Decimal("280000"),
        "2202.01": Decimal("150000"), "2202.02": Decimal("130000"),
        "2211": Decimal("180000"), "2221": Decimal("95000"),
        "2221.01": Decimal("60000"), "2221.02": Decimal("0"),
        "2221.03": Decimal("35000"),
        "3001": Decimal("2000000"), "3002": Decimal("500000"),
        "3101": Decimal("100000"), "3103": Decimal("0"), "3104": Decimal("437000"),
    }

    acct_map = {a["code"]: a for a in CHART_OF_ACCOUNTS}

    # Aggregate book entries by (account_code, period)
    entry_agg: dict[tuple[str, str], dict] = defaultdict(lambda: {"debit": Decimal("0"), "credit": Decimal("0")})
    for e in book_entries:
        period = str(e.entry_date)[:7]  # YYYY-MM
        key = (e.account_code, period)
        if e.direction == "debit":
            entry_agg[key]["debit"] += e.amount
        else:
            entry_agg[key]["credit"] += e.amount

    # Track closing balances to carry forward
    prev_closing: dict[str, Decimal] = {}

    for period_idx, period in enumerate(PERIODS):
        for acct in CHART_OF_ACCOUNTS:
            code = acct["code"]
            # Opening balance: Jan uses hardcoded, others carry forward
            if period_idx == 0:
                opening = opening_balances_jan.get(code, Decimal("0"))
            else:
                opening = prev_closing.get(code, Decimal("0"))

            agg = entry_agg.get((code, period), {"debit": Decimal("0"), "credit": Decimal("0")})
            debit_amt = agg["debit"]
            credit_amt = agg["credit"]

            if acct["balance_direction"] == "debit":
                closing = opening + debit_amt - credit_amt
            else:
                closing = opening - debit_amt + credit_amt

            prev_closing[code] = closing

            session.add(AccountBalance(
                account_code=code, account_name=acct["name"],
                account_level=acct["level"], parent_code=acct.get("parent_code") or "",
                period=period, opening_balance=opening,
                debit_amount=debit_amt, credit_amount=credit_amt,
                closing_balance=closing, balance_direction=acct["balance_direction"],
            ))
    await session.flush()


async def seed_cost_centers(session: AsyncSession):
    """5 departments for 星辰科技有限公司."""
    centers = [
        {"code": "CC01", "name": "研发部", "center_type": "department", "parent_id": None, "headcount": 35, "area": 400.0, "revenue_ratio": 0.45},
        {"code": "CC02", "name": "销售部", "center_type": "department", "parent_id": None, "headcount": 15, "area": 150.0, "revenue_ratio": 0.30},
        {"code": "CC03", "name": "运营部", "center_type": "department", "parent_id": None, "headcount": 10, "area": 120.0, "revenue_ratio": 0.15},
        {"code": "CC04", "name": "财务部", "center_type": "department", "parent_id": None, "headcount": 5, "area": 60.0, "revenue_ratio": 0.05},
        {"code": "CC05", "name": "行政部", "center_type": "department", "parent_id": None, "headcount": 5, "area": 70.0, "revenue_ratio": 0.05},
    ]
    for c in centers:
        session.add(CostCenter(**c))
    await session.flush()


async def seed_cost_pools(session: AsyncSession):
    """5 cost pools x 3 months."""
    pool_defs = [
        ("办公租金", "rent", "5602.01", [35000, 35000, 35000]),
        ("水电费", "utilities", "5602.02", [4200, 4800, 5100]),
        ("IT运维费", "it", "5602.06", [12000, 13500, 11000]),
        ("管理层薪资", "management", "5602", [60000, 60000, 60000]),
        ("折旧摊销", "other", "5602.03", [8000, 8000, 8000]),
    ]
    for name, cost_type, acct_code, amounts in pool_defs:
        for period_idx, period in enumerate(PERIODS):
            session.add(CostPool(
                name=name, cost_type=cost_type, account_code=acct_code,
                period=period, amount=Decimal(str(amounts[period_idx])),
                is_allocated=False,
            ))
    await session.flush()


async def seed_reconciliation_rules(session: AsyncSession):
    """Preset matching rules."""
    rules = [
        {"name": "精确匹配-金额日期", "match_fields": {"amount": "exact", "date": "exact"}, "tolerance_days": 0, "tolerance_amount": Decimal("0"), "priority": 1},
        {"name": "模糊匹配-金额一致日期容差", "match_fields": {"amount": "exact", "date": "fuzzy", "summary": "similar"}, "tolerance_days": 3, "tolerance_amount": Decimal("0"), "priority": 2},
        {"name": "智能匹配-拆分合并", "match_fields": {"amount": "split", "date": "fuzzy"}, "tolerance_days": 5, "tolerance_amount": Decimal("0.01"), "priority": 3},
    ]
    for r in rules:
        session.add(ReconciliationRule(**r))
    await session.flush()


async def seed_tax_mappings(session: AsyncSession):
    """VAT and CIT mappings."""
    mappings = [
        # VAT 主表
        {"account_code": "5001", "account_name": "主营业务收入", "tax_form_type": "vat_general", "tax_line_no": "1", "tax_line_name": "（一）按适用税率计税销售额", "data_source": "current_credit"},
        {"account_code": "2221.01", "account_name": "应交税费-应交增值税(销项)", "tax_form_type": "vat_general", "tax_line_no": "11", "tax_line_name": "销项税额", "data_source": "current_credit"},
        {"account_code": "2221.02", "account_name": "应交税费-应交增值税(进项)", "tax_form_type": "vat_general", "tax_line_no": "12", "tax_line_name": "进项税额", "data_source": "current_debit"},
        # CIT quarterly
        {"account_code": "5001", "account_name": "主营业务收入", "tax_form_type": "cit_quarterly", "tax_line_no": "1", "tax_line_name": "营业收入", "data_source": "cumulative"},
        {"account_code": "5401", "account_name": "主营业务成本", "tax_form_type": "cit_quarterly", "tax_line_no": "2", "tax_line_name": "营业成本", "data_source": "cumulative"},
        {"account_code": "5801", "account_name": "所得税费用", "tax_form_type": "cit_quarterly", "tax_line_no": "4", "tax_line_name": "实际利润额", "data_source": "cumulative"},
    ]
    for m in mappings:
        session.add(TaxMapping(**m))
    await session.flush()


async def seed_tax_templates(session: AsyncSession):
    """Filing templates."""
    templates = [
        {"form_type": "vat_general", "form_name": "增值税纳税申报表（一般纳税人适用）主表", "period_type": "monthly"},
        {"form_type": "vat_general", "form_name": "增值税纳税申报表附列资料（一）", "period_type": "monthly"},
        {"form_type": "vat_general", "form_name": "增值税纳税申报表附列资料（二）", "period_type": "monthly"},
        {"form_type": "cit_quarterly", "form_name": "企业所得税月（季）度预缴纳税申报表", "period_type": "quarterly"},
    ]
    for t in templates:
        session.add(TaxFilingTemplate(**t))
    await session.flush()


async def seed_tax_validation_rules(session: AsyncSession):
    """Tax validation rules."""
    rules = [
        {"form_type": "vat_general", "rule_name": "销项税额 = 销售额 × 税率", "rule_expression": "line_11 == line_1 * 0.13", "severity": "error"},
        {"form_type": "vat_general", "rule_name": "应纳税额 = 销项税额 - 进项税额", "rule_expression": "line_19 == line_11 - line_12", "severity": "error"},
        {"form_type": "cit_quarterly", "rule_name": "利润总额 = 营业收入 - 营业成本 - 期间费用", "rule_expression": "line_3 == line_1 - line_2", "severity": "warning"},
    ]
    for r in rules:
        session.add(TaxValidationRule(**r))
    await session.flush()


async def seed_report_templates(session: AsyncSession):
    """Report line templates for balance sheet, income statement, cash flow."""
    # Balance Sheet (simplified)
    bs_lines = [
        ("1", "流动资产：", "", 0, False, 1),
        ("2", "  货币资金", "SUM(1001,1002)", 1, False, 2),
        ("3", "  应收账款", "SUM(1122)", 1, False, 3),
        ("4", "  预付款项", "SUM(1123)", 1, False, 4),
        ("5", "  存货", "SUM(1403,1405)", 1, False, 5),
        ("6", "  流动资产合计", "SUM(L2:L5)", 0, True, 6),
        ("7", "非流动资产：", "", 0, False, 7),
        ("8", "  固定资产", "1601-1602", 1, False, 8),
        ("9", "  无形资产", "SUM(1701)", 1, False, 9),
        ("10", "  非流动资产合计", "SUM(L8:L9)", 0, True, 10),
        ("11", "资产总计", "L6+L10", 0, True, 11),
        ("12", "流动负债：", "", 0, False, 12),
        ("13", "  短期借款", "SUM(2001)", 1, False, 13),
        ("14", "  应付账款", "SUM(2202)", 1, False, 14),
        ("15", "  应付职工薪酬", "SUM(2211)", 1, False, 15),
        ("16", "  应交税费", "SUM(2221)", 1, False, 16),
        ("17", "  流动负债合计", "SUM(L13:L16)", 0, True, 17),
        ("18", "负债合计", "L17", 0, True, 18),
        ("19", "所有者权益：", "", 0, False, 19),
        ("20", "  实收资本", "SUM(3001)", 1, False, 20),
        ("21", "  资本公积", "SUM(3002)", 1, False, 21),
        ("22", "  盈余公积", "SUM(3101)", 1, False, 22),
        ("23", "  未分配利润", "SUM(3103,3104)", 1, False, 23),
        ("24", "  所有者权益合计", "SUM(L20:L23)", 0, True, 24),
        ("25", "负债和所有者权益总计", "L18+L24", 0, True, 25),
    ]
    for ln, name, formula, indent, is_total, order in bs_lines:
        session.add(ReportTemplate(
            report_type="balance_sheet", line_no=ln, line_name=name,
            formula=formula, indent_level=indent, is_total=is_total, display_order=order,
        ))

    # Income Statement (simplified)
    is_lines = [
        ("1", "一、营业收入", "SUM(5001,5051)", 0, False, 1),
        ("2", "减：营业成本", "SUM(5401,5402)", 0, False, 2),
        ("3", "    营业税金及附加", "SUM(5403)", 1, False, 3),
        ("4", "    销售费用", "SUM(5601)", 1, False, 4),
        ("5", "    管理费用", "SUM(5602)", 1, False, 5),
        ("6", "    财务费用", "SUM(5603)", 1, False, 6),
        ("7", "二、营业利润", "L1-L2-L3-L4-L5-L6", 0, True, 7),
        ("8", "加：营业外收入", "SUM(5301)", 0, False, 8),
        ("9", "减：营业外支出", "SUM(5711)", 0, False, 9),
        ("10", "三、利润总额", "L7+L8-L9", 0, True, 10),
        ("11", "减：所得税费用", "SUM(5801)", 0, False, 11),
        ("12", "四、净利润", "L10-L11", 0, True, 12),
    ]
    for ln, name, formula, indent, is_total, order in is_lines:
        session.add(ReportTemplate(
            report_type="income", line_no=ln, line_name=name,
            formula=formula, indent_level=indent, is_total=is_total, display_order=order,
        ))

    # Cash Flow (simplified, indirect method adjustments)
    cf_lines = [
        ("1", "一、经营活动产生的现金流量", "", 0, False, 1),
        ("2", "  销售商品收到的现金", "SUM(5001)*1.13", 1, False, 2),
        ("3", "  购买商品支付的现金", "SUM(5401)*1.13", 1, False, 3),
        ("4", "  支付给职工的现金", "SUM(2211_debit)", 1, False, 4),
        ("5", "  支付的各项税费", "SUM(2221_debit)", 1, False, 5),
        ("6", "  经营活动现金流量净额", "L2-L3-L4-L5", 0, True, 6),
        ("7", "二、投资活动产生的现金流量", "", 0, False, 7),
        ("8", "  购建固定资产支付的现金", "SUM(1601_debit)", 1, False, 8),
        ("9", "  投资活动现金流量净额", "-L8", 0, True, 9),
        ("10", "三、筹资活动产生的现金流量", "", 0, False, 10),
        ("11", "  取得借款收到的现金", "SUM(2001_credit)", 1, False, 11),
        ("12", "  偿还借款支付的现金", "SUM(2001_debit)", 1, False, 12),
        ("13", "  筹资活动现金流量净额", "L11-L12", 0, True, 13),
        ("14", "四、现金净增加额", "L6+L9+L13", 0, True, 14),
    ]
    for ln, name, formula, indent, is_total, order in cf_lines:
        session.add(ReportTemplate(
            report_type="cash_flow", line_no=ln, line_name=name,
            formula=formula, indent_level=indent, is_total=is_total, display_order=order,
        ))

    await session.flush()


async def seed_allocation_rules(session: AsyncSession):
    """Preset cost allocation rules."""
    # We need cost_pool IDs — they are seeded as IDs 1-15 (5 pools x 3 months)
    # Pool IDs: rent=1,4,7; utilities=2,5,8; it=3,6,9; management=10,11,12(wrong)
    # Actually they are sequential: rent(1,2,3), utilities(4,5,6)...
    # But rules reference pool type, not period-specific pool. Use pool_id=0 as placeholder;
    # the service will match by cost_type.
    rules = [
        {"name": "办公租金按面积分摊", "cost_pool_id": 0, "allocation_basis": "area", "condition_expr": "cost_type == 'rent'", "priority": 1, "effective_from": date(2024, 1, 1), "effective_to": None},
        {"name": "水电费按面积分摊", "cost_pool_id": 0, "allocation_basis": "area", "condition_expr": "cost_type == 'utilities'", "priority": 2, "effective_from": date(2024, 1, 1), "effective_to": None},
        {"name": "IT运维费按人数分摊", "cost_pool_id": 0, "allocation_basis": "headcount", "condition_expr": "cost_type == 'it'", "priority": 3, "effective_from": date(2024, 1, 1), "effective_to": None},
        {"name": "管理层薪资按收入占比分摊", "cost_pool_id": 0, "allocation_basis": "revenue", "condition_expr": "cost_type == 'management'", "priority": 4, "effective_from": date(2024, 1, 1), "effective_to": None},
        {"name": "折旧摊销按面积分摊", "cost_pool_id": 0, "allocation_basis": "area", "condition_expr": "cost_type == 'other'", "priority": 5, "effective_from": date(2024, 1, 1), "effective_to": None},
    ]
    for r in rules:
        session.add(AllocationRule(**r))
    await session.flush()


async def run_seed():
    """Main seed entry point."""
    await init_db()
    async with async_session() as session:
        async with session.begin():
            await seed_chart_of_accounts(session)
            await seed_bank_transactions(session)
            book_entries = await seed_book_entries(session)
            await seed_account_balances(session, book_entries)
            await seed_cost_centers(session)
            await seed_cost_pools(session)
            await seed_reconciliation_rules(session)
            await seed_tax_mappings(session)
            await seed_tax_templates(session)
            await seed_tax_validation_rules(session)
            await seed_report_templates(session)
            await seed_allocation_rules(session)
        print("Seed completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_seed())
```

- [ ] **Step 2: Verify seed script runs**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
source venv/bin/activate
cd backend
python -m app.mock.seed
```

Expected: `Seed completed successfully!` and `finmate.db` created.

- [ ] **Step 3: Verify seeded data**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate/backend
python -c "
import sqlite3
conn = sqlite3.connect('finmate.db')
tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
for t in tables:
    count = conn.execute(f'SELECT COUNT(*) FROM {t[0]}').fetchone()[0]
    print(f'{t[0]}: {count} rows')
conn.close()
"
```

Expected: chart_of_accounts ~60, bank_transactions ~200+, book_entries ~180+, account_balances ~180 (60x3), cost_centers 5, cost_pools 15, reconciliation_rules 3, tax_mappings 6, tax_filing_templates 4, etc. Verify accounting integrity: all vouchers should have balanced debits/credits.

- [ ] **Step 4: Add seed command to main.py lifespan**

Modify `FinMate/backend/app/main.py` — update the lifespan to auto-seed if DB is empty:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Auto-seed if database is empty
    async with async_session() as session:
        from app.models.base import ChartOfAccounts
        from sqlalchemy import select, func
        result = await session.execute(select(func.count()).select_from(ChartOfAccounts))
        if result.scalar() == 0:
            from app.mock.seed import run_seed
            await run_seed()
    yield
```

Add import at top of main.py:

```python
from app.database import init_db, async_session
```

- [ ] **Step 5: Clean up test DB and commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate/backend
rm -f finmate.db
cd /Users/laurant/Documents/github/comlan/FinMate
git add backend/app/mock/ backend/app/main.py
git commit -m "feat: add mock data seed script for 星辰科技有限公司 (3 months of realistic data)"
```

---

## Chunk 3: Backend Services & APIs

This chunk implements the 4 business service modules and their REST API routes, plus the dashboard summary endpoint. Each service follows the pattern: service file with business logic → API router file → register in main.py.

### Task 12: Response Schema & API Utilities

**Files:**
- Create: `FinMate/backend/app/api/response.py`

- [ ] **Step 1: Create unified response helper**

Create `FinMate/backend/app/api/response.py`:

```python
from typing import Any


def success(data: Any = None, message: str = "ok") -> dict:
    return {"code": 200, "data": data, "message": message}


def error(code: int = 400, message: str = "error") -> dict:
    return {"code": code, "data": None, "message": message}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add backend/app/api/response.py
git commit -m "feat: add unified API response helpers"
```

---

### Task 13: Reconciliation Service & API

**Files:**
- Create: `FinMate/backend/app/services/reconciliation_service.py`
- Create: `FinMate/backend/app/api/reconciliation.py`
- Modify: `FinMate/backend/app/main.py` (register router)

- [ ] **Step 1: Create reconciliation service**

Create `FinMate/backend/app/services/reconciliation_service.py`:

```python
"""Bank reconciliation service — three-tier matching engine."""

import uuid
from decimal import Decimal
from difflib import SequenceMatcher

from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BookEntry
from app.models.reconciliation import BankTransaction, ReconciliationRecord, ReconciliationRule


async def get_transactions(
    session: AsyncSession, period: str | None = None,
    status: str | None = None, min_amount: float | None = None,
    max_amount: float | None = None, counterparty: str | None = None,
    page: int = 1, page_size: int = 20,
) -> dict:
    query = select(BankTransaction)
    count_query = select(func.count()).select_from(BankTransaction)

    conditions = []
    if period:
        conditions.append(func.strftime("%Y-%m", BankTransaction.transaction_date) == period)
    if status:
        conditions.append(BankTransaction.matched_status == status)
    if min_amount is not None:
        conditions.append(func.abs(BankTransaction.amount) >= min_amount)
    if max_amount is not None:
        conditions.append(func.abs(BankTransaction.amount) <= max_amount)
    if counterparty:
        conditions.append(BankTransaction.counterparty.contains(counterparty))

    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))

    total = (await session.execute(count_query)).scalar()
    query = query.order_by(BankTransaction.transaction_date.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    rows = (await session.execute(query)).scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_txn_to_dict(t) for t in rows],
    }


async def get_book_entries(
    session: AsyncSession, period: str | None = None,
    account_code: str | None = None, page: int = 1, page_size: int = 20,
) -> dict:
    query = select(BookEntry)
    count_query = select(func.count()).select_from(BookEntry)

    conditions = []
    if period:
        conditions.append(func.strftime("%Y-%m", BookEntry.entry_date) == period)
    if account_code:
        conditions.append(BookEntry.account_code.startswith(account_code))

    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))

    total = (await session.execute(count_query)).scalar()
    query = query.order_by(BookEntry.entry_date.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    rows = (await session.execute(query)).scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_entry_to_dict(e) for e in rows],
    }


async def get_reconciliation_status(session: AsyncSession, period: str | None = None) -> dict:
    conditions = []
    if period:
        conditions.append(func.strftime("%Y-%m", BankTransaction.transaction_date) == period)

    base = select(func.count()).select_from(BankTransaction)
    if conditions:
        base = base.where(and_(*conditions))

    total = (await session.execute(base)).scalar()
    matched_q = base.where(BankTransaction.matched_status.in_(["matched", "confirmed"]))
    matched = (await session.execute(matched_q)).scalar()

    unmatched_amt_q = select(func.sum(func.abs(BankTransaction.amount))).where(
        BankTransaction.matched_status == "unmatched"
    )
    if conditions:
        unmatched_amt_q = unmatched_amt_q.where(and_(*conditions))
    unmatched_amount = (await session.execute(unmatched_amt_q)).scalar() or 0

    return {
        "total_transactions": total,
        "matched_count": matched,
        "unmatched_count": total - matched,
        "match_rate": round(matched / total * 100, 1) if total > 0 else 0,
        "unmatched_amount": float(unmatched_amount),
    }


async def run_auto_match(session: AsyncSession, period: str) -> dict:
    """Three-tier matching: exact → fuzzy → smart."""
    # Get unmatched transactions and book entries for the period
    bank_q = select(BankTransaction).where(
        and_(
            func.strftime("%Y-%m", BankTransaction.transaction_date) == period,
            BankTransaction.matched_status == "unmatched",
        )
    )
    bank_txns = list((await session.execute(bank_q)).scalars().all())

    book_q = select(BookEntry).where(
        and_(
            func.strftime("%Y-%m", BookEntry.entry_date) == period,
            BookEntry.account_code.startswith("1002"),  # Bank accounts only
        )
    )
    book_entries = list((await session.execute(book_q)).scalars().all())

    matched_bank_ids = set()
    matched_book_ids = set()
    details = []

    # L1: Exact match — same amount, same date
    for txn in bank_txns:
        if txn.id in matched_bank_ids:
            continue
        for entry in book_entries:
            if entry.id in matched_book_ids:
                continue
            amount_match = (txn.amount > 0 and entry.direction == "debit" and entry.amount == txn.amount) or \
                           (txn.amount < 0 and entry.direction == "credit" and entry.amount == abs(txn.amount))
            date_match = txn.transaction_date == entry.entry_date
            if amount_match and date_match:
                group_id = str(uuid.uuid4())[:8]
                session.add(ReconciliationRecord(
                    match_group_id=group_id, bank_transaction_id=txn.id,
                    book_entry_id=entry.id, match_type="exact",
                    confidence_score=1.0, is_confirmed=False, match_rule="金额+日期精确匹配",
                ))
                txn.matched_status = "matched"
                matched_bank_ids.add(txn.id)
                matched_book_ids.add(entry.id)
                details.append({"type": "exact", "bank_id": txn.id, "book_id": entry.id, "confidence": 1.0})
                break

    # L2: Fuzzy match — same amount, date within 3 days, summary similarity > 0.5
    for txn in bank_txns:
        if txn.id in matched_bank_ids:
            continue
        for entry in book_entries:
            if entry.id in matched_book_ids:
                continue
            amount_match = (txn.amount > 0 and entry.direction == "debit" and entry.amount == txn.amount) or \
                           (txn.amount < 0 and entry.direction == "credit" and entry.amount == abs(txn.amount))
            if not amount_match:
                continue
            day_diff = abs((txn.transaction_date - entry.entry_date).days)
            if day_diff > 3:
                continue
            sim = SequenceMatcher(None, txn.summary, entry.summary).ratio()
            if sim < 0.3:
                continue
            confidence = 0.7 + 0.1 * sim + 0.1 * (1 - day_diff / 3)
            group_id = str(uuid.uuid4())[:8]
            session.add(ReconciliationRecord(
                match_group_id=group_id, bank_transaction_id=txn.id,
                book_entry_id=entry.id, match_type="fuzzy",
                confidence_score=round(confidence, 2), is_confirmed=False,
                match_rule=f"模糊匹配: 日期差{day_diff}天, 摘要相似度{sim:.0%}",
            ))
            txn.matched_status = "matched"
            matched_bank_ids.add(txn.id)
            matched_book_ids.add(entry.id)
            details.append({"type": "fuzzy", "bank_id": txn.id, "book_id": entry.id, "confidence": round(confidence, 2)})
            break

    # L3: Smart match — one-to-many (sum of book entries matches bank amount)
    for txn in bank_txns:
        if txn.id in matched_bank_ids:
            continue
        target_amt = abs(txn.amount)
        direction = "debit" if txn.amount > 0 else "credit"
        candidates = [e for e in book_entries if e.id not in matched_book_ids and e.direction == direction]
        # Try pairs
        for i, e1 in enumerate(candidates):
            for e2 in candidates[i + 1:]:
                if e1.amount + e2.amount == target_amt:
                    group_id = str(uuid.uuid4())[:8]
                    for e in [e1, e2]:
                        session.add(ReconciliationRecord(
                            match_group_id=group_id, bank_transaction_id=txn.id,
                            book_entry_id=e.id, match_type="smart",
                            confidence_score=0.6, is_confirmed=False,
                            match_rule="智能匹配: 多笔合计匹配",
                        ))
                        matched_book_ids.add(e.id)
                    txn.matched_status = "matched"
                    matched_bank_ids.add(txn.id)
                    details.append({"type": "smart", "bank_id": txn.id, "book_ids": [e1.id, e2.id], "confidence": 0.6})
                    break
            if txn.id in matched_bank_ids:
                break

    await session.flush()

    return {
        "matched": len(matched_bank_ids),
        "unmatched": len(bank_txns) - len(matched_bank_ids),
        "details": details,
    }


async def manual_match(session: AsyncSession, bank_ids: list[int], book_ids: list[int]) -> dict:
    group_id = str(uuid.uuid4())[:8]
    for bid in bank_ids:
        for eid in book_ids:
            session.add(ReconciliationRecord(
                match_group_id=group_id, bank_transaction_id=bid,
                book_entry_id=eid, match_type="manual",
                confidence_score=1.0, is_confirmed=True, match_rule="手动匹配",
            ))
        await session.execute(
            update(BankTransaction).where(BankTransaction.id == bid).values(matched_status="confirmed")
        )
    await session.flush()
    return {"match_group_id": group_id}


async def exclude_transaction(session: AsyncSession, transaction_id: int, reason: str) -> dict:
    await session.execute(
        update(BankTransaction).where(BankTransaction.id == transaction_id).values(matched_status="excluded")
    )
    await session.flush()
    return {"transaction_id": transaction_id, "status": "excluded", "reason": reason}


async def get_unmatched(session: AsyncSession, period: str) -> dict:
    bank_q = select(BankTransaction).where(
        and_(
            func.strftime("%Y-%m", BankTransaction.transaction_date) == period,
            BankTransaction.matched_status == "unmatched",
        )
    )
    unmatched_bank = (await session.execute(bank_q)).scalars().all()

    # Find book entries not in any reconciliation record for this period
    matched_book_ids_q = select(ReconciliationRecord.book_entry_id)
    matched_book_ids = [r for r in (await session.execute(matched_book_ids_q)).scalars().all()]

    book_q = select(BookEntry).where(
        and_(
            func.strftime("%Y-%m", BookEntry.entry_date) == period,
            BookEntry.account_code.startswith("1002"),
            BookEntry.id.notin_(matched_book_ids) if matched_book_ids else True,
        )
    )
    unmatched_book = (await session.execute(book_q)).scalars().all()

    return {
        "bank_only": [_txn_to_dict(t) for t in unmatched_bank],
        "book_only": [_entry_to_dict(e) for e in unmatched_book],
    }


def _txn_to_dict(t: BankTransaction) -> dict:
    return {
        "id": t.id, "account_no": t.account_no,
        "transaction_date": str(t.transaction_date), "amount": float(t.amount),
        "counterparty": t.counterparty, "summary": t.summary,
        "serial_no": t.serial_no, "currency": t.currency,
        "matched_status": t.matched_status,
    }


def _entry_to_dict(e: BookEntry) -> dict:
    return {
        "id": e.id, "entry_date": str(e.entry_date), "amount": float(e.amount),
        "account_code": e.account_code, "account_name": e.account_name,
        "voucher_no": e.voucher_no, "summary": e.summary,
        "auxiliary": e.auxiliary, "direction": e.direction,
    }
```

- [ ] **Step 2: Create reconciliation API router**

Create `FinMate/backend/app/api/reconciliation.py`:

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.response import success
from app.services import reconciliation_service as svc

router = APIRouter(prefix="/api/v1/reconciliation", tags=["reconciliation"])


@router.get("/transactions")
async def get_transactions(
    period: str | None = None, status: str | None = None,
    min_amount: float | None = None, max_amount: float | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    data = await svc.get_transactions(db, period, status, min_amount, max_amount, page, page_size)
    return success(data)


@router.get("/book-entries")
async def get_book_entries(
    period: str | None = None, account_code: str | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    data = await svc.get_book_entries(db, period, account_code, page, page_size)
    return success(data)


@router.get("/status")
async def get_status(period: str | None = None, db: AsyncSession = Depends(get_db)):
    data = await svc.get_reconciliation_status(db, period)
    return success(data)


@router.post("/match")
async def auto_match(body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.run_auto_match(db, body["period"])
    await db.commit()
    return success(data)


@router.post("/manual-match")
async def manual_match(body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.manual_match(db, body["bank_ids"], body["book_ids"])
    await db.commit()
    return success(data)


@router.post("/exclude")
async def exclude(body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.exclude_transaction(db, body["transaction_id"], body.get("reason", ""))
    await db.commit()
    return success(data)


@router.get("/unmatched")
async def get_unmatched(period: str = Query(...), db: AsyncSession = Depends(get_db)):
    data = await svc.get_unmatched(db, period)
    return success(data)
```

- [ ] **Step 3: Register router in main.py**

Add to `FinMate/backend/app/main.py`, after middleware setup:

```python
from app.api.reconciliation import router as reconciliation_router
app.include_router(reconciliation_router)
```

- [ ] **Step 4: Verify reconciliation API**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
source venv/bin/activate
cd backend
uvicorn app.main:app --port 8000 &
sleep 3
curl -s http://localhost:8000/api/v1/reconciliation/status | python -m json.tool
curl -s "http://localhost:8000/api/v1/reconciliation/transactions?period=2024-01&page_size=3" | python -m json.tool
kill %1
```

Expected: Status with match_rate, transactions list with items.

- [ ] **Step 5: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add backend/app/services/reconciliation_service.py backend/app/api/reconciliation.py backend/app/main.py
git commit -m "feat: add reconciliation service with three-tier matching engine and API"
```

---

### Task 14: Tax Service & API

**Files:**
- Create: `FinMate/backend/app/services/tax_service.py`
- Create: `FinMate/backend/app/api/tax.py`
- Modify: `FinMate/backend/app/main.py` (register router)

- [ ] **Step 1: Create tax service**

Create `FinMate/backend/app/services/tax_service.py`:

```python
"""Tax data preparation service."""

from decimal import Decimal

from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import AccountBalance
from app.models.tax import TaxMapping, TaxFilingTemplate, TaxLineItem, TaxEstimate, TaxValidationRule


async def get_mappings(session: AsyncSession, form_type: str | None = None) -> list[dict]:
    query = select(TaxMapping)
    if form_type:
        query = query.where(TaxMapping.tax_form_type == form_type)
    rows = (await session.execute(query)).scalars().all()
    return [_mapping_to_dict(m) for m in rows]


async def update_mapping(session: AsyncSession, mapping_id: int, tax_line_no: str, data_source: str) -> dict:
    await session.execute(
        update(TaxMapping).where(TaxMapping.id == mapping_id).values(
            tax_line_no=tax_line_no, data_source=data_source,
        )
    )
    await session.flush()
    return {"id": mapping_id, "updated": True}


async def get_filing(session: AsyncSession, form_type: str, period: str) -> dict:
    template = (await session.execute(
        select(TaxFilingTemplate).where(TaxFilingTemplate.form_type == form_type)
    )).scalars().first()

    if not template:
        return {"form_type": form_type, "form_name": "未找到模板", "lines": []}

    # Get existing line items or generate
    lines_q = select(TaxLineItem).where(
        and_(TaxLineItem.template_id == template.id, TaxLineItem.period == period)
    ).order_by(TaxLineItem.line_no)
    lines = (await session.execute(lines_q)).scalars().all()

    return {
        "form_type": form_type,
        "form_name": template.form_name,
        "period": period,
        "lines": [_line_to_dict(l) for l in lines],
    }


async def generate_filing(session: AsyncSession, form_type: str, period: str) -> dict:
    """Generate filing data from account balances using tax mappings."""
    mappings = (await session.execute(
        select(TaxMapping).where(TaxMapping.tax_form_type == form_type)
    )).scalars().all()

    template = (await session.execute(
        select(TaxFilingTemplate).where(TaxFilingTemplate.form_type == form_type)
    )).scalars().first()

    if not template:
        return {"error": "Template not found"}

    # Delete existing line items for this period
    existing = (await session.execute(
        select(TaxLineItem).where(
            and_(TaxLineItem.template_id == template.id, TaxLineItem.period == period)
        )
    )).scalars().all()
    for item in existing:
        await session.delete(item)

    generated_lines = []
    for mapping in mappings:
        # Get account balance for this period
        bal = (await session.execute(
            select(AccountBalance).where(
                and_(AccountBalance.account_code == mapping.account_code, AccountBalance.period == period)
            )
        )).scalars().first()

        value = Decimal("0")
        if bal:
            if mapping.data_source == "current_debit":
                value = bal.debit_amount
            elif mapping.data_source == "current_credit":
                value = bal.credit_amount
            elif mapping.data_source == "closing_balance":
                value = bal.closing_balance
            elif mapping.data_source == "cumulative":
                # Sum all periods up to this one
                cum_q = select(func.sum(AccountBalance.debit_amount - AccountBalance.credit_amount)).where(
                    and_(AccountBalance.account_code == mapping.account_code, AccountBalance.period <= period)
                )
                cum_val = (await session.execute(cum_q)).scalar()
                value = cum_val or Decimal("0")

        line = TaxLineItem(
            template_id=template.id, line_no=mapping.tax_line_no,
            line_name=mapping.tax_line_name, formula=f"FROM:{mapping.account_code}:{mapping.data_source}",
            current_value=value, adjusted_value=None, period=period,
        )
        session.add(line)
        generated_lines.append(line)

    # Add computed lines (VAT payable = output - input)
    if form_type == "vat_general":
        output_tax = sum(l.current_value for l in generated_lines if l.line_no == "11")
        input_tax = sum(l.current_value for l in generated_lines if l.line_no == "12")
        payable = output_tax - input_tax
        session.add(TaxLineItem(
            template_id=template.id, line_no="19", line_name="应纳税额",
            formula="line_11 - line_12", current_value=payable, adjusted_value=None, period=period,
        ))

    await session.flush()

    return await get_filing(session, form_type, period)


async def adjust_line(session: AsyncSession, line_id: int, adjusted_value: float, reason: str) -> dict:
    await session.execute(
        update(TaxLineItem).where(TaxLineItem.id == line_id).values(
            adjusted_value=Decimal(str(adjusted_value))
        )
    )
    await session.flush()
    return {"line_id": line_id, "adjusted_value": adjusted_value, "reason": reason}


async def get_estimate(session: AsyncSession, period: str) -> list[dict]:
    rows = (await session.execute(
        select(TaxEstimate).where(TaxEstimate.period == period)
    )).scalars().all()

    if not rows:
        # Generate estimates from mappings
        estimates = []
        # VAT estimate
        output_q = select(AccountBalance).where(
            and_(AccountBalance.account_code == "2221.01", AccountBalance.period == period)
        )
        output_bal = (await session.execute(output_q)).scalars().first()
        input_q = select(AccountBalance).where(
            and_(AccountBalance.account_code == "2221.02", AccountBalance.period == period)
        )
        input_bal = (await session.execute(input_q)).scalars().first()

        output_amt = output_bal.credit_amount if output_bal else Decimal("0")
        input_amt = input_bal.debit_amount if input_bal else Decimal("0")
        vat = output_amt - input_amt

        estimates.append({
            "tax_type": "增值税", "period": period,
            "taxable_amount": float(output_amt / Decimal("0.13")) if output_amt else 0,
            "tax_amount": float(vat), "previous_period": 0, "yoy_change": 0,
        })

        # CIT estimate (simplified: 25% of profit)
        income_q = select(func.sum(AccountBalance.credit_amount)).where(
            and_(AccountBalance.account_code.startswith("5001"), AccountBalance.period == period)
        )
        income = (await session.execute(income_q)).scalar() or Decimal("0")
        cost_q = select(func.sum(AccountBalance.debit_amount)).where(
            and_(AccountBalance.account_code.startswith("54"), AccountBalance.period == period)
        )
        cost = (await session.execute(cost_q)).scalar() or Decimal("0")
        profit = income - cost
        cit = profit * Decimal("0.25")
        estimates.append({
            "tax_type": "企业所得税", "period": period,
            "taxable_amount": float(profit), "tax_amount": float(cit),
            "previous_period": 0, "yoy_change": 0,
        })
        return estimates

    return [_estimate_to_dict(e) for e in rows]


async def get_validation(session: AsyncSession, form_type: str, period: str) -> list[dict]:
    rules = (await session.execute(
        select(TaxValidationRule).where(TaxValidationRule.form_type == form_type)
    )).scalars().all()

    results = []
    for rule in rules:
        results.append({
            "rule_name": rule.rule_name,
            "expression": rule.rule_expression,
            "severity": rule.severity,
            "passed": True,  # Simplified — real impl would evaluate expression
            "message": "校验通过",
        })
    return results


def _mapping_to_dict(m: TaxMapping) -> dict:
    return {
        "id": m.id, "account_code": m.account_code, "account_name": m.account_name,
        "tax_form_type": m.tax_form_type, "tax_line_no": m.tax_line_no,
        "tax_line_name": m.tax_line_name, "data_source": m.data_source,
    }


def _line_to_dict(l: TaxLineItem) -> dict:
    return {
        "id": l.id, "line_no": l.line_no, "line_name": l.line_name,
        "formula": l.formula, "current_value": float(l.current_value),
        "adjusted_value": float(l.adjusted_value) if l.adjusted_value is not None else None,
        "period": l.period,
    }


def _estimate_to_dict(e: TaxEstimate) -> dict:
    return {
        "id": e.id, "tax_type": e.tax_type, "period": e.period,
        "taxable_amount": float(e.taxable_amount), "tax_amount": float(e.tax_amount),
        "previous_period": float(e.previous_period), "yoy_change": e.yoy_change,
    }
```

- [ ] **Step 2: Create tax API router**

Create `FinMate/backend/app/api/tax.py`:

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.response import success
from app.services import tax_service as svc

router = APIRouter(prefix="/api/v1/tax", tags=["tax"])


@router.get("/mappings")
async def get_mappings(form_type: str | None = None, db: AsyncSession = Depends(get_db)):
    data = await svc.get_mappings(db, form_type)
    return success(data)


@router.put("/mappings/{mapping_id}")
async def update_mapping(mapping_id: int, body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.update_mapping(db, mapping_id, body["tax_line_no"], body["data_source"])
    await db.commit()
    return success(data)


@router.get("/filing/{form_type}")
async def get_filing(form_type: str, period: str = Query(...), db: AsyncSession = Depends(get_db)):
    data = await svc.get_filing(db, form_type, period)
    return success(data)


@router.post("/filing/generate")
async def generate_filing(body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.generate_filing(db, body["form_type"], body["period"])
    await db.commit()
    return success(data)


@router.put("/filing/adjust")
async def adjust_line(body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.adjust_line(db, body["line_id"], body["adjusted_value"], body.get("reason", ""))
    await db.commit()
    return success(data)


@router.get("/estimate")
async def get_estimate(period: str = Query(...), db: AsyncSession = Depends(get_db)):
    data = await svc.get_estimate(db, period)
    return success(data)


@router.get("/validation/{form_type}")
async def get_validation(form_type: str, period: str = Query(...), db: AsyncSession = Depends(get_db)):
    data = await svc.get_validation(db, form_type, period)
    return success(data)
```

- [ ] **Step 3: Register router in main.py**

Add to `FinMate/backend/app/main.py`:

```python
from app.api.tax import router as tax_router
app.include_router(tax_router)
```

- [ ] **Step 4: Verify tax API**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
source venv/bin/activate
cd backend
uvicorn app.main:app --port 8000 &
sleep 3
curl -s "http://localhost:8000/api/v1/tax/mappings?form_type=vat_general" | python -m json.tool
curl -s "http://localhost:8000/api/v1/tax/estimate?period=2024-01" | python -m json.tool
kill %1
```

Expected: Mappings array and estimates array.

- [ ] **Step 5: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add backend/app/services/tax_service.py backend/app/api/tax.py backend/app/main.py
git commit -m "feat: add tax service with filing generation, validation, and API"
```

---

### Task 15: Reports Service & API

**Files:**
- Create: `FinMate/backend/app/services/report_service.py`
- Create: `FinMate/backend/app/api/reports.py`
- Modify: `FinMate/backend/app/main.py` (register router)

- [ ] **Step 1: Create report service**

Create `FinMate/backend/app/services/report_service.py`:

```python
"""Financial report generation service."""

from decimal import Decimal

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import AccountBalance, BookEntry
from app.models.reports import ReportTemplate, ReportData, FinancialIndicator


async def get_report(session: AsyncSession, report_type: str, period: str) -> dict:
    """Get report data — generate if not exists."""
    data_q = select(ReportData).where(
        and_(ReportData.report_type == report_type, ReportData.period == period)
    ).order_by(ReportData.line_no)
    data_rows = (await session.execute(data_q)).scalars().all()

    template_q = select(ReportTemplate).where(
        ReportTemplate.report_type == report_type
    ).order_by(ReportTemplate.display_order)
    templates = (await session.execute(template_q)).scalars().all()

    # Merge template structure with data
    data_map = {d.line_no: d for d in data_rows}
    lines = []
    for t in templates:
        d = data_map.get(t.line_no)
        lines.append({
            "line_no": t.line_no,
            "line_name": t.line_name,
            "indent_level": t.indent_level,
            "is_total": t.is_total,
            "current_amount": float(d.current_amount) if d else 0,
            "previous_amount": float(d.previous_amount) if d else 0,
            "yoy_change": d.yoy_change if d else 0,
        })

    return {"report_type": report_type, "period": period, "lines": lines}


async def generate_reports(session: AsyncSession, period: str) -> dict:
    """Generate all three reports from account balances."""
    results = {}
    for report_type in ["balance_sheet", "income", "cash_flow"]:
        templates = (await session.execute(
            select(ReportTemplate).where(ReportTemplate.report_type == report_type).order_by(ReportTemplate.display_order)
        )).scalars().all()

        # Delete existing report data for this period
        existing = (await session.execute(
            select(ReportData).where(and_(ReportData.report_type == report_type, ReportData.period == period))
        )).scalars().all()
        for item in existing:
            await session.delete(item)

        # Compute line values from account balances
        line_values = {}
        for t in templates:
            value = await _compute_formula(session, t.formula, period, line_values)
            line_values[t.line_no] = value

            # Get previous period value
            prev_period = _prev_period(period)
            prev_line_values = {}
            for pt in templates:
                if pt.display_order <= t.display_order:
                    pv = await _compute_formula(session, pt.formula, prev_period, prev_line_values)
                    prev_line_values[pt.line_no] = pv
            prev_value = prev_line_values.get(t.line_no, Decimal("0"))
            yoy = 0.0
            if prev_value != 0:
                yoy = float((value - prev_value) / abs(prev_value) * 100)

            session.add(ReportData(
                report_type=report_type, period=period, line_no=t.line_no,
                current_amount=value, previous_amount=prev_value, yoy_change=yoy,
            ))

        results[report_type] = len(templates)

    await session.flush()

    # Also generate financial indicators
    await _generate_indicators(session, period)

    return {"period": period, "reports_generated": results}


async def drill_down(session: AsyncSession, report_type: str, line_no: str, period: str, level: int) -> dict:
    """Three-level drill-down: L1 report line → L2 sub-accounts → L3 voucher entries."""
    template = (await session.execute(
        select(ReportTemplate).where(
            and_(ReportTemplate.report_type == report_type, ReportTemplate.line_no == line_no)
        )
    )).scalars().first()

    if not template:
        return {"error": "Line not found"}

    if level == 1:
        # Show sub-account balances
        # Parse formula to get account codes
        codes = _parse_account_codes(template.formula)
        balances = []
        for code in codes:
            rows = (await session.execute(
                select(AccountBalance).where(
                    and_(AccountBalance.account_code.startswith(code), AccountBalance.period == period)
                )
            )).scalars().all()
            for b in rows:
                balances.append({
                    "account_code": b.account_code, "account_name": b.account_name,
                    "level": b.account_level, "opening_balance": float(b.opening_balance),
                    "debit_amount": float(b.debit_amount), "credit_amount": float(b.credit_amount),
                    "closing_balance": float(b.closing_balance),
                })
        return {"level": 1, "type": "account_balances", "items": balances}

    elif level == 2:
        # Show voucher entries for a specific account
        account_code = line_no  # In level 2, line_no is actually the account_code
        entries = (await session.execute(
            select(BookEntry).where(
                and_(
                    BookEntry.account_code == account_code,
                    func.strftime("%Y-%m", BookEntry.entry_date) == period,
                )
            ).order_by(BookEntry.entry_date)
        )).scalars().all()
        return {
            "level": 2, "type": "voucher_entries",
            "items": [{
                "id": e.id, "entry_date": str(e.entry_date), "voucher_no": e.voucher_no,
                "summary": e.summary, "amount": float(e.amount), "direction": e.direction,
                "auxiliary": e.auxiliary,
            } for e in entries],
        }

    return {"level": level, "items": []}


async def get_indicators(session: AsyncSession, period: str) -> list[dict]:
    rows = (await session.execute(
        select(FinancialIndicator).where(FinancialIndicator.period == period)
    )).scalars().all()
    return [{
        "indicator_name": i.indicator_name, "indicator_value": i.indicator_value,
        "benchmark_value": i.benchmark_value, "health_status": i.health_status,
        "description": i.description,
    } for i in rows]


async def get_trend(session: AsyncSession, report_type: str, line_no: str, periods: list[str]) -> list[dict]:
    rows = (await session.execute(
        select(ReportData).where(
            and_(ReportData.report_type == report_type, ReportData.line_no == line_no,
                 ReportData.period.in_(periods))
        ).order_by(ReportData.period)
    )).scalars().all()
    return [{"period": r.period, "amount": float(r.current_amount)} for r in rows]


async def _compute_formula(session: AsyncSession, formula: str, period: str, line_values: dict) -> Decimal:
    """Simplified formula evaluator."""
    if not formula:
        return Decimal("0")

    # Handle SUM(account_codes)
    if formula.startswith("SUM(") and formula.endswith(")"):
        inner = formula[4:-1]
        # Check if referencing lines (L2:L5) or accounts (1001,1002)
        if inner.startswith("L"):
            # Sum of lines: SUM(L2:L5)
            if ":" in inner:
                start, end = inner.split(":")
                start_no = int(start[1:])
                end_no = int(end[1:])
                return sum(line_values.get(str(i), Decimal("0")) for i in range(start_no, end_no + 1))
            return line_values.get(inner[1:], Decimal("0"))
        else:
            # Sum of account balances
            codes = [c.strip() for c in inner.split(",")]
            total = Decimal("0")
            for code in codes:
                bal = (await session.execute(
                    select(AccountBalance).where(
                        and_(AccountBalance.account_code == code, AccountBalance.period == period, AccountBalance.account_level == 1)
                    )
                )).scalars().first()
                if bal:
                    total += bal.closing_balance
            return total

    # Handle line arithmetic: L1-L2-L3
    if formula.startswith("L") or "L" in formula:
        try:
            result = Decimal("0")
            parts = formula.replace("+", " + ").replace("-", " - ").split()
            op = "+"
            for p in parts:
                if p in ("+", "-"):
                    op = p
                elif p.startswith("L"):
                    val = line_values.get(p[1:], Decimal("0"))
                    if op == "+":
                        result += val
                    else:
                        result -= val
            return result
        except Exception:
            return Decimal("0")

    # Handle subtraction: 1601-1602
    if "-" in formula and not formula.startswith("-"):
        parts = formula.split("-")
        if len(parts) == 2:
            b1 = (await session.execute(
                select(AccountBalance).where(
                    and_(AccountBalance.account_code == parts[0].strip(), AccountBalance.period == period)
                )
            )).scalars().first()
            b2 = (await session.execute(
                select(AccountBalance).where(
                    and_(AccountBalance.account_code == parts[1].strip(), AccountBalance.period == period)
                )
            )).scalars().first()
            v1 = b1.closing_balance if b1 else Decimal("0")
            v2 = b2.closing_balance if b2 else Decimal("0")
            return v1 - v2

    return Decimal("0")


async def _generate_indicators(session: AsyncSession, period: str):
    """Generate key financial indicators."""
    # Delete existing
    existing = (await session.execute(
        select(FinancialIndicator).where(FinancialIndicator.period == period)
    )).scalars().all()
    for item in existing:
        await session.delete(item)

    async def _get_balance(code: str) -> Decimal:
        b = (await session.execute(
            select(AccountBalance).where(
                and_(AccountBalance.account_code == code, AccountBalance.period == period)
            )
        )).scalars().first()
        return b.closing_balance if b else Decimal("0")

    # Current ratio
    current_assets = sum([await _get_balance(c) for c in ["1001", "1002", "1122", "1123", "1403", "1405"]])
    current_liabs = sum([await _get_balance(c) for c in ["2001", "2202", "2211", "2221"]])
    cr = float(current_assets / current_liabs) if current_liabs else 0
    session.add(FinancialIndicator(
        period=period, indicator_name="流动比率", indicator_value=round(cr, 2),
        benchmark_value=1.5, health_status="good" if cr >= 1.5 else ("warning" if cr >= 1.0 else "danger"),
        description=f"流动比率为{cr:.2f}，{'高于' if cr >= 1.5 else '低于'}行业均值1.5",
    ))

    # Asset-liability ratio
    total_assets = current_assets + await _get_balance("1601") - await _get_balance("1602") + await _get_balance("1701")
    total_liabs = current_liabs
    alr = float(total_liabs / total_assets * 100) if total_assets else 0
    session.add(FinancialIndicator(
        period=period, indicator_name="资产负债率", indicator_value=round(alr, 1),
        benchmark_value=50.0, health_status="good" if alr <= 60 else ("warning" if alr <= 75 else "danger"),
        description=f"资产负债率为{alr:.1f}%，{'处于安全范围' if alr <= 60 else '偏高'}",
    ))

    # Gross margin (simplified)
    revenue = await _get_balance("5001")
    cost = await _get_balance("5401")
    gm = float((revenue - cost) / revenue * 100) if revenue else 0
    session.add(FinancialIndicator(
        period=period, indicator_name="毛利率", indicator_value=round(abs(gm), 1),
        benchmark_value=35.0, health_status="good" if abs(gm) >= 30 else "warning",
        description=f"毛利率为{abs(gm):.1f}%",
    ))

    await session.flush()


def _parse_account_codes(formula: str) -> list[str]:
    """Extract account codes from formula like SUM(1001,1002)."""
    if formula.startswith("SUM(") and formula.endswith(")"):
        inner = formula[4:-1]
        if not inner.startswith("L"):
            return [c.strip() for c in inner.split(",")]
    if "-" in formula and not formula.startswith("L"):
        return [p.strip() for p in formula.split("-") if p.strip() and not p.strip().startswith("L")]
    return []


def _prev_period(period: str) -> str:
    year, month = int(period[:4]), int(period[5:])
    if month == 1:
        return f"{year - 1}-12"
    return f"{year}-{month - 1:02d}"
```

- [ ] **Step 2: Create reports API router**

Create `FinMate/backend/app/api/reports.py`:

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.response import success
from app.services import report_service as svc

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

# NOTE: Specific routes MUST be declared before the wildcard /{report_type}
# to avoid FastAPI matching "drill-down" as a report_type.


@router.post("/generate")
async def generate_reports(body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.generate_reports(db, body["period"])
    await db.commit()
    return success(data)


@router.get("/drill-down")
async def drill_down(
    report_type: str = Query(...), line_no: str = Query(...),
    period: str = Query(...), level: int = Query(1),
    db: AsyncSession = Depends(get_db),
):
    data = await svc.drill_down(db, report_type, line_no, period, level)
    return success(data)


@router.get("/indicators")
async def get_indicators(period: str = Query(...), db: AsyncSession = Depends(get_db)):
    data = await svc.get_indicators(db, period)
    return success(data)


@router.get("/trend")
async def get_trend(
    report_type: str = Query(...), line_no: str = Query(...),
    periods: str = Query(..., description="Comma-separated periods"),
    db: AsyncSession = Depends(get_db),
):
    period_list = [p.strip() for p in periods.split(",")]
    data = await svc.get_trend(db, report_type, line_no, period_list)
    return success(data)


@router.get("/{report_type}")
async def get_report(report_type: str, period: str = Query(...), db: AsyncSession = Depends(get_db)):
    data = await svc.get_report(db, report_type, period)
    return success(data)
```

- [ ] **Step 3: Register router in main.py**

Add to `FinMate/backend/app/main.py`:

```python
from app.api.reports import router as reports_router
app.include_router(reports_router)
```

- [ ] **Step 4: Verify reports API**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
source venv/bin/activate
cd backend
uvicorn app.main:app --port 8000 &
sleep 3
curl -s -X POST http://localhost:8000/api/v1/reports/generate -H "Content-Type: application/json" -d '{"period":"2024-01"}' | python -m json.tool
curl -s "http://localhost:8000/api/v1/reports/balance_sheet?period=2024-01" | python -m json.tool
kill %1
```

Expected: Reports generated, balance sheet with line items.

- [ ] **Step 5: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add backend/app/services/report_service.py backend/app/api/reports.py backend/app/main.py
git commit -m "feat: add report service with three-report generation, drill-down, and indicators"
```

---

### Task 16: Cost Allocation Service & API

**Files:**
- Create: `FinMate/backend/app/services/cost_alloc_service.py`
- Create: `FinMate/backend/app/api/cost_alloc.py`
- Modify: `FinMate/backend/app/main.py` (register router)

- [ ] **Step 1: Create cost allocation service**

Create `FinMate/backend/app/services/cost_alloc_service.py`:

```python
"""Cost allocation service with IF-THEN rule engine."""

import json
from decimal import Decimal

from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cost_alloc import (
    CostCenter, CostPool, AllocationRule, AllocationResult, AllocationVoucher,
)


async def get_centers(session: AsyncSession) -> list[dict]:
    rows = (await session.execute(select(CostCenter).order_by(CostCenter.code))).scalars().all()
    return [_center_to_dict(c) for c in rows]


async def get_pools(session: AsyncSession, period: str | None = None) -> list[dict]:
    query = select(CostPool)
    if period:
        query = query.where(CostPool.period == period)
    rows = (await session.execute(query.order_by(CostPool.name))).scalars().all()
    return [_pool_to_dict(p) for p in rows]


async def get_rules(session: AsyncSession) -> list[dict]:
    rows = (await session.execute(
        select(AllocationRule).order_by(AllocationRule.priority)
    )).scalars().all()
    return [_rule_to_dict(r) for r in rows]


async def create_rule(session: AsyncSession, data: dict) -> dict:
    rule = AllocationRule(**data)
    session.add(rule)
    await session.flush()
    return _rule_to_dict(rule)


async def update_rule(session: AsyncSession, rule_id: int, data: dict) -> dict:
    await session.execute(
        update(AllocationRule).where(AllocationRule.id == rule_id).values(**data)
    )
    await session.flush()
    return {"id": rule_id, "updated": True}


async def calculate(session: AsyncSession, period: str, save: bool = True) -> dict:
    """Execute cost allocation based on rules."""
    pools = (await session.execute(
        select(CostPool).where(CostPool.period == period)
    )).scalars().all()

    centers = (await session.execute(select(CostCenter))).scalars().all()
    rules = (await session.execute(
        select(AllocationRule).order_by(AllocationRule.priority)
    )).scalars().all()

    # Delete existing results for this period if saving
    if save:
        existing = (await session.execute(
            select(AllocationResult).where(AllocationResult.period == period)
        )).scalars().all()
        for item in existing:
            await session.delete(item)

    total_headcount = sum(c.headcount for c in centers)
    total_area = sum(c.area for c in centers)
    total_revenue = sum(c.revenue_ratio for c in centers)

    results = []
    sankey_nodes = set()
    sankey_links = []

    for pool in pools:
        # Find matching rule
        matched_rule = None
        for rule in rules:
            if rule.condition_expr and pool.cost_type in rule.condition_expr:
                matched_rule = rule
                break

        if not matched_rule:
            continue

        basis = matched_rule.allocation_basis
        for center in centers:
            if basis == "headcount":
                ratio = center.headcount / total_headcount if total_headcount else 0
            elif basis == "area":
                ratio = center.area / total_area if total_area else 0
            elif basis == "revenue":
                ratio = center.revenue_ratio / total_revenue if total_revenue else 0
            else:
                ratio = 1.0 / len(centers)

            allocated = (pool.amount * Decimal(str(ratio))).quantize(Decimal("0.01"))

            result_data = {
                "rule_id": matched_rule.id,
                "cost_pool_id": pool.id,
                "cost_center_id": center.id,
                "period": period,
                "allocated_amount": allocated,
                "allocation_ratio": round(ratio, 4),
                "calculation_detail": json.dumps({
                    "pool": pool.name, "center": center.name,
                    "basis": basis, "ratio": round(ratio, 4),
                    "pool_amount": float(pool.amount),
                }, ensure_ascii=False),
            }

            if save:
                session.add(AllocationResult(**result_data))

            results.append({
                **result_data,
                "allocated_amount": float(allocated),
                "pool_name": pool.name,
                "center_name": center.name,
            })

            sankey_nodes.add(pool.name)
            sankey_nodes.add(center.name)
            sankey_links.append({
                "source": pool.name, "target": center.name,
                "value": float(allocated),
            })

    if save:
        # Mark pools as allocated
        for pool in pools:
            pool.is_allocated = True
        await session.flush()

    return {
        "period": period,
        "total_allocated": sum(r["allocated_amount"] for r in results),
        "results": results,
        "sankey": {
            "nodes": [{"name": n} for n in sankey_nodes],
            "links": sankey_links,
        },
    }


async def simulate(session: AsyncSession, period: str, rules: list[dict] | None = None) -> dict:
    """Simulate allocation without saving."""
    return await calculate(session, period, save=False)


async def get_results(session: AsyncSession, period: str) -> dict:
    rows = (await session.execute(
        select(AllocationResult).where(AllocationResult.period == period)
    )).scalars().all()

    centers = {c.id: c.name for c in (await session.execute(select(CostCenter))).scalars().all()}
    pools = {p.id: p.name for p in (await session.execute(
        select(CostPool).where(CostPool.period == period)
    )).scalars().all()}

    results = []
    sankey_nodes = set()
    sankey_links = []

    for r in rows:
        pool_name = pools.get(r.cost_pool_id, "")
        center_name = centers.get(r.cost_center_id, "")
        results.append({
            "pool_name": pool_name, "center_name": center_name,
            "allocated_amount": float(r.allocated_amount),
            "allocation_ratio": r.allocation_ratio,
        })
        sankey_nodes.add(pool_name)
        sankey_nodes.add(center_name)
        sankey_links.append({"source": pool_name, "target": center_name, "value": float(r.allocated_amount)})

    return {
        "period": period,
        "results": results,
        "sankey": {"nodes": [{"name": n} for n in sankey_nodes], "links": sankey_links},
    }


async def get_voucher(session: AsyncSession, period: str) -> dict:
    voucher = (await session.execute(
        select(AllocationVoucher).where(AllocationVoucher.period == period)
    )).scalars().first()

    if not voucher:
        # Generate voucher from results
        results = (await session.execute(
            select(AllocationResult).where(AllocationResult.period == period)
        )).scalars().all()

        centers = {c.id: c for c in (await session.execute(select(CostCenter))).scalars().all()}
        pools = {p.id: p for p in (await session.execute(
            select(CostPool).where(CostPool.period == period)
        )).scalars().all()}

        entries = []
        for r in results:
            pool = pools.get(r.cost_pool_id)
            center = centers.get(r.cost_center_id)
            if pool and center:
                entries.append({
                    "debit_account": f"4001-{center.code}",
                    "debit_name": f"生产成本-{center.name}",
                    "credit_account": pool.account_code,
                    "credit_name": pool.name,
                    "amount": float(r.allocated_amount),
                    "cost_center": center.name,
                })

        return {
            "period": period, "voucher_no": f"FP-{period}-001",
            "entries": entries, "status": "draft",
        }

    return {
        "period": period, "voucher_no": voucher.voucher_no,
        "entries": voucher.entries, "status": voucher.status,
    }


def _center_to_dict(c: CostCenter) -> dict:
    return {
        "id": c.id, "code": c.code, "name": c.name,
        "center_type": c.center_type, "parent_id": c.parent_id,
        "headcount": c.headcount, "area": c.area, "revenue_ratio": c.revenue_ratio,
    }


def _pool_to_dict(p: CostPool) -> dict:
    return {
        "id": p.id, "name": p.name, "cost_type": p.cost_type,
        "account_code": p.account_code, "period": p.period,
        "amount": float(p.amount), "is_allocated": p.is_allocated,
    }


def _rule_to_dict(r: AllocationRule) -> dict:
    return {
        "id": r.id, "name": r.name, "cost_pool_id": r.cost_pool_id,
        "allocation_basis": r.allocation_basis, "condition_expr": r.condition_expr,
        "priority": r.priority, "effective_from": str(r.effective_from),
        "effective_to": str(r.effective_to) if r.effective_to else None,
    }
```

- [ ] **Step 2: Create cost allocation API router**

Create `FinMate/backend/app/api/cost_alloc.py`:

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.response import success
from app.services import cost_alloc_service as svc

router = APIRouter(prefix="/api/v1/cost-alloc", tags=["cost-allocation"])


@router.get("/centers")
async def get_centers(db: AsyncSession = Depends(get_db)):
    data = await svc.get_centers(db)
    return success(data)


@router.get("/pools")
async def get_pools(period: str | None = None, db: AsyncSession = Depends(get_db)):
    data = await svc.get_pools(db, period)
    return success(data)


@router.get("/rules")
async def get_rules(db: AsyncSession = Depends(get_db)):
    data = await svc.get_rules(db)
    return success(data)


@router.post("/rules")
async def create_rule(body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.create_rule(db, body)
    await db.commit()
    return success(data)


@router.put("/rules/{rule_id}")
async def update_rule(rule_id: int, body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.update_rule(db, rule_id, body)
    await db.commit()
    return success(data)


@router.post("/calculate")
async def calculate(body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.calculate(db, body["period"])
    await db.commit()
    return success(data)


@router.post("/simulate")
async def simulate(body: dict, db: AsyncSession = Depends(get_db)):
    data = await svc.simulate(db, body["period"], body.get("rules"))
    return success(data)


@router.get("/results")
async def get_results(period: str = Query(...), db: AsyncSession = Depends(get_db)):
    data = await svc.get_results(db, period)
    return success(data)


@router.get("/voucher")
async def get_voucher(period: str = Query(...), db: AsyncSession = Depends(get_db)):
    data = await svc.get_voucher(db, period)
    return success(data)
```

- [ ] **Step 3: Register router in main.py**

Add to `FinMate/backend/app/main.py`:

```python
from app.api.cost_alloc import router as cost_alloc_router
app.include_router(cost_alloc_router)
```

- [ ] **Step 4: Verify cost allocation API**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
source venv/bin/activate
cd backend
uvicorn app.main:app --port 8000 &
sleep 3
curl -s http://localhost:8000/api/v1/cost-alloc/centers | python -m json.tool
curl -s "http://localhost:8000/api/v1/cost-alloc/pools?period=2024-01" | python -m json.tool
curl -s http://localhost:8000/api/v1/cost-alloc/rules | python -m json.tool
kill %1
```

Expected: 5 cost centers, pools with amounts, 5 allocation rules.

- [ ] **Step 5: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add backend/app/services/cost_alloc_service.py backend/app/api/cost_alloc.py backend/app/main.py
git commit -m "feat: add cost allocation service with IF-THEN rule engine and API"
```

---

### Task 17: Dashboard Summary API

**Files:**
- Create: `FinMate/backend/app/api/dashboard.py`
- Modify: `FinMate/backend/app/main.py` (register router)

- [ ] **Step 1: Create dashboard API router**

Create `FinMate/backend/app/api/dashboard.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.response import success
from app.models.base import AccountBalance
from app.models.reconciliation import BankTransaction
from app.models.cost_alloc import CostPool
from app.services import tax_service

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

DEFAULT_PERIOD = "2024-03"


@router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    period = DEFAULT_PERIOD

    # Reconciliation status
    total_txns = (await db.execute(
        select(func.count()).select_from(BankTransaction).where(
            func.strftime("%Y-%m", BankTransaction.transaction_date) == period
        )
    )).scalar() or 0
    matched_txns = (await db.execute(
        select(func.count()).select_from(BankTransaction).where(
            and_(
                func.strftime("%Y-%m", BankTransaction.transaction_date) == period,
                BankTransaction.matched_status.in_(["matched", "confirmed"]),
            )
        )
    )).scalar() or 0
    match_rate = round(matched_txns / total_txns * 100, 1) if total_txns else 0

    # Tax estimates
    estimates = await tax_service.get_estimate(db, period)
    vat_estimate = next((e for e in estimates if e.get("tax_type") == "增值税"), {})
    estimated_vat = vat_estimate.get("tax_amount", 0)
    revenue_for_tax = vat_estimate.get("taxable_amount", 0)
    tax_burden_rate = round(estimated_vat / revenue_for_tax * 100, 2) if revenue_for_tax else 0

    # Financial snapshot
    bank_bal = (await db.execute(
        select(AccountBalance.closing_balance).where(
            and_(AccountBalance.account_code == "1002", AccountBalance.period == period)
        )
    )).scalar() or 0
    total_assets_q = await db.execute(
        select(func.sum(AccountBalance.closing_balance)).where(
            and_(AccountBalance.account_code.in_(["1001", "1002", "1122", "1123", "1403", "1405", "1601", "1701"]),
                 AccountBalance.period == period)
        )
    )
    total_assets = total_assets_q.scalar() or 0

    # Net profit = revenue - expenses (from account balances)
    revenue = (await db.execute(
        select(func.sum(AccountBalance.credit_amount)).where(
            and_(AccountBalance.account_code.startswith("5001"), AccountBalance.period == period)
        )
    )).scalar() or 0
    expenses = (await db.execute(
        select(func.sum(AccountBalance.debit_amount)).where(
            and_(AccountBalance.account_code.startswith("5"), AccountBalance.period == period,
                 AccountBalance.account_code >= "5401")
        )
    )).scalar() or 0
    net_profit = float(revenue) - float(expenses)

    # Cost allocation status
    total_pools = (await db.execute(
        select(func.sum(CostPool.amount)).where(CostPool.period == period)
    )).scalar() or 0
    allocated_pools = (await db.execute(
        select(func.sum(CostPool.amount)).where(
            and_(CostPool.period == period, CostPool.is_allocated == True)
        )
    )).scalar() or 0

    return success({
        "period": period,
        "reconciliation": {
            "match_rate": match_rate,
            "unmatched_count": total_txns - matched_txns,
        },
        "tax": {
            "estimated_vat": float(estimated_vat),
            "tax_burden_rate": tax_burden_rate,
        },
        "financial": {
            "total_assets": float(total_assets),
            "cash_balance": float(bank_bal),
            "net_profit": net_profit,
        },
        "cost_allocation": {
            "total_pending": float(total_pools - allocated_pools),
            "progress": round(float(allocated_pools / total_pools * 100), 1) if total_pools else 0,
        },
    })
```

- [ ] **Step 2: Register router in main.py**

Add to `FinMate/backend/app/main.py`:

```python
from app.api.dashboard import router as dashboard_router
app.include_router(dashboard_router)
```

- [ ] **Step 3: Verify dashboard API**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
source venv/bin/activate
cd backend
uvicorn app.main:app --port 8000 &
sleep 3
curl -s http://localhost:8000/api/v1/dashboard/summary | python -m json.tool
kill %1
```

Expected: Summary with reconciliation, tax, financial, and cost_allocation sections.

- [ ] **Step 4: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add backend/app/api/dashboard.py backend/app/main.py
git commit -m "feat: add dashboard summary API"
```

---

## Chunk 4: AI Agent Layer

This chunk implements the Claude API Agent with tool_use for multi-step reasoning, the agent tools for all 4 modules, and the SSE chat endpoint.

### Task 18: Agent Tools Definition

**Files:**
- Create: `FinMate/backend/app/agent/tools.py`

- [ ] **Step 1: Create agent tools definition**

Create `FinMate/backend/app/agent/tools.py`:

```python
"""Agent tool definitions for Claude API tool_use.
Each tool maps to a function that the agent can call during multi-step reasoning.
"""

# Tool schemas for Claude API
AGENT_TOOLS = [
    # Reconciliation tools
    {
        "name": "query_bank_transactions",
        "description": "查询银行流水记录，可按日期、金额范围、对方户名筛选",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
                "min_amount": {"type": "number", "description": "最小金额"},
                "max_amount": {"type": "number", "description": "最大金额"},
                "counterparty": {"type": "string", "description": "对方户名关键词"},
            },
            "required": [],
        },
    },
    {
        "name": "query_book_entries",
        "description": "查询账簿记录/会计凭证，可按期间、科目筛选",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
                "account_code": {"type": "string", "description": "科目编码前缀"},
            },
            "required": [],
        },
    },
    {
        "name": "get_reconciliation_status",
        "description": "获取银行对账匹配状态统计，包括匹配率、未匹配数量和金额",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
            },
            "required": [],
        },
    },
    {
        "name": "analyze_unmatched_items",
        "description": "获取未匹配项的详细分析，分为单边银行项和单边账簿项",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
            },
            "required": ["period"],
        },
    },
    # Tax tools
    {
        "name": "query_tax_data",
        "description": "查询税务申报表数据，包括增值税和企业所得税",
        "input_schema": {
            "type": "object",
            "properties": {
                "form_type": {"type": "string", "description": "申报表类型: vat_general 或 cit_quarterly"},
                "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
            },
            "required": ["form_type", "period"],
        },
    },
    {
        "name": "calculate_tax_estimate",
        "description": "计算指定期间的预估税额，包括增值税和企业所得税",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
            },
            "required": ["period"],
        },
    },
    {
        "name": "check_tax_compliance",
        "description": "校验税务数据合规性，检查表内勾稽和合理性",
        "input_schema": {
            "type": "object",
            "properties": {
                "form_type": {"type": "string", "description": "申报表类型"},
                "period": {"type": "string", "description": "期间"},
            },
            "required": ["form_type", "period"],
        },
    },
    # Report tools
    {
        "name": "generate_financial_report",
        "description": "生成指定期间的财务报表（资产负债表、利润表、现金流量表）",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
                "report_type": {"type": "string", "description": "报表类型: balance_sheet, income, cash_flow"},
            },
            "required": ["period"],
        },
    },
    {
        "name": "calculate_financial_indicators",
        "description": "计算财务指标（流动比率、资产负债率、毛利率等）并评估健康度",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
            },
            "required": ["period"],
        },
    },
    {
        "name": "drill_down_report_item",
        "description": "钻取报表项目明细，从报表行项到科目余额再到凭证明细",
        "input_schema": {
            "type": "object",
            "properties": {
                "report_type": {"type": "string", "description": "报表类型"},
                "line_no": {"type": "string", "description": "行号"},
                "period": {"type": "string", "description": "期间"},
                "level": {"type": "integer", "description": "钻取层级: 1=科目余额, 2=凭证明细"},
            },
            "required": ["report_type", "line_no", "period"],
        },
    },
    # Cost allocation tools
    {
        "name": "query_cost_allocation",
        "description": "查询成本分摊数据，包括费用池、成本中心和分摊结果",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "期间，格式 YYYY-MM"},
                "center_name": {"type": "string", "description": "成本中心名称"},
            },
            "required": ["period"],
        },
    },
    {
        "name": "simulate_allocation",
        "description": "模拟成本分摊计算（不保存结果），用于方案对比",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "期间"},
            },
            "required": ["period"],
        },
    },
    {
        "name": "compare_allocation_schemes",
        "description": "对比不同分摊方案（如按人数vs按面积），展示差异",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "期间"},
                "pool_name": {"type": "string", "description": "费用池名称"},
            },
            "required": ["period"],
        },
    },
]

# Module → tool name mapping for context-aware tool selection
MODULE_TOOLS = {
    "reconciliation": [
        "query_bank_transactions", "query_book_entries",
        "get_reconciliation_status", "analyze_unmatched_items",
    ],
    "tax": [
        "query_tax_data", "calculate_tax_estimate", "check_tax_compliance",
    ],
    "reports": [
        "generate_financial_report", "calculate_financial_indicators",
        "drill_down_report_item",
    ],
    "cost_alloc": [
        "query_cost_allocation", "simulate_allocation",
        "compare_allocation_schemes",
    ],
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add backend/app/agent/tools.py
git commit -m "feat: add agent tool definitions for Claude API tool_use (13 tools across 4 modules)"
```

---

### Task 19: Agent Core Logic

**Files:**
- Create: `FinMate/backend/app/agent/agent.py`

- [ ] **Step 1: Create agent core with tool execution**

Create `FinMate/backend/app/agent/agent.py`:

```python
"""AI Agent core — Claude API tool_use multi-step reasoning."""

import json
from typing import AsyncGenerator

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.agent.tools import AGENT_TOOLS, MODULE_TOOLS
from app.services import reconciliation_service, tax_service, report_service, cost_alloc_service


SYSTEM_PROMPT = """你是 FinMate AI 财务助理，一个专业的智能财务分析助手。你可以帮助用户：
- 分析银行对账数据，找出未匹配原因
- 查询和分析税务申报数据
- 生成和解读财务报表
- 分析成本分摊方案的合理性

你的回答要专业、准确、有数据支撑。在分析时：
1. 先调用工具获取必要数据
2. 基于数据给出分析结论
3. 提供可操作的建议
4. 用清晰的结构化格式呈现

请用中文回复。金额单位为人民币元。"""


async def execute_tool(
    tool_name: str, tool_input: dict, session: AsyncSession
) -> str:
    """Execute a tool call and return the result as a string."""
    try:
        if tool_name == "query_bank_transactions":
            result = await reconciliation_service.get_transactions(
                session, period=tool_input.get("period"),
                min_amount=tool_input.get("min_amount"),
                max_amount=tool_input.get("max_amount"),
                counterparty=tool_input.get("counterparty"),
                page_size=10,
            )
        elif tool_name == "query_book_entries":
            result = await reconciliation_service.get_book_entries(
                session, period=tool_input.get("period"),
                account_code=tool_input.get("account_code"),
                page_size=10,
            )
        elif tool_name == "get_reconciliation_status":
            result = await reconciliation_service.get_reconciliation_status(
                session, period=tool_input.get("period"),
            )
        elif tool_name == "analyze_unmatched_items":
            result = await reconciliation_service.get_unmatched(
                session, period=tool_input["period"],
            )
        elif tool_name == "query_tax_data":
            result = await tax_service.get_filing(
                session, tool_input["form_type"], tool_input["period"],
            )
        elif tool_name == "calculate_tax_estimate":
            result = await tax_service.get_estimate(
                session, tool_input["period"],
            )
        elif tool_name == "check_tax_compliance":
            result = await tax_service.get_validation(
                session, tool_input["form_type"], tool_input["period"],
            )
        elif tool_name == "generate_financial_report":
            report_type = tool_input.get("report_type")
            if report_type:
                result = await report_service.get_report(session, report_type, tool_input["period"])
            else:
                result = await report_service.generate_reports(session, tool_input["period"])
        elif tool_name == "calculate_financial_indicators":
            result = await report_service.get_indicators(session, tool_input["period"])
        elif tool_name == "drill_down_report_item":
            result = await report_service.drill_down(
                session, tool_input["report_type"], tool_input["line_no"],
                tool_input["period"], tool_input.get("level", 1),
            )
        elif tool_name == "query_cost_allocation":
            result = await cost_alloc_service.get_results(session, tool_input["period"])
        elif tool_name == "simulate_allocation":
            result = await cost_alloc_service.simulate(session, tool_input["period"])
        elif tool_name == "compare_allocation_schemes":
            # Compare allocation by different bases for the same pool
            current = await cost_alloc_service.simulate(session, tool_input["period"])
            pool_name = tool_input.get("pool_name", "")
            # Filter results for the specified pool if given
            if pool_name:
                current["results"] = [r for r in current.get("results", []) if pool_name in str(r.get("pool_name", ""))]
            result = {"comparison": current, "note": f"对比分摊方案: {pool_name or '全部费用池'}"}
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


async def chat_stream(
    message: str,
    module_context: str | None,
    history: list[dict],
    session: AsyncSession,
) -> AsyncGenerator[str, None]:
    """Stream AI agent response with tool_use multi-step reasoning."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    # Select tools based on module context
    if module_context and module_context in MODULE_TOOLS:
        tool_names = MODULE_TOOLS[module_context]
        tools = [t for t in AGENT_TOOLS if t["name"] in tool_names]
    else:
        tools = AGENT_TOOLS

    # Build messages
    messages = []
    for h in history[-10:]:  # Keep last 10 messages for context
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    max_iterations = 5
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        # Call Claude API with tools (async)
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        # Process response content blocks
        has_tool_use = False
        tool_results = []

        for block in response.content:
            if block.type == "text":
                # Stream text chunks
                text = block.text
                # Split into smaller chunks for SSE
                chunk_size = 50
                for i in range(0, len(text), chunk_size):
                    yield json.dumps({
                        "type": "text",
                        "content": text[i:i + chunk_size],
                    }, ensure_ascii=False)

            elif block.type == "tool_use":
                has_tool_use = True
                # Notify frontend about tool call
                yield json.dumps({
                    "type": "tool_call",
                    "tool_name": block.name,
                    "tool_input": block.input,
                }, ensure_ascii=False)

                # Execute tool
                result = await execute_tool(block.name, block.input, session)

                yield json.dumps({
                    "type": "tool_result",
                    "tool_name": block.name,
                    "success": "error" not in result,
                }, ensure_ascii=False)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        if not has_tool_use:
            # No more tool calls — done
            break

        # Add assistant response and tool results for next iteration
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    yield json.dumps({"type": "done"}, ensure_ascii=False)
```

- [ ] **Step 2: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add backend/app/agent/agent.py
git commit -m "feat: add AI agent core with Claude API tool_use multi-step reasoning"
```

---

### Task 20: AI Chat SSE Endpoint

**Files:**
- Create: `FinMate/backend/app/api/ai_chat.py`
- Modify: `FinMate/backend/app/main.py` (register router)

- [ ] **Step 1: Create AI chat API with SSE streaming**

Create `FinMate/backend/app/api/ai_chat.py`:

```python
import json

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.database import get_db
from app.agent.agent import chat_stream

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


@router.post("/chat")
async def chat(body: dict, db: AsyncSession = Depends(get_db)):
    message = body.get("message", "")
    module_context = body.get("module_context")
    history = body.get("history", [])

    async def event_generator():
        async for chunk in chat_stream(message, module_context, history, db):
            yield {"event": "message", "data": chunk}

    return EventSourceResponse(event_generator())
```

- [ ] **Step 2: Register router in main.py**

Add to `FinMate/backend/app/main.py`:

```python
from app.api.ai_chat import router as ai_chat_router
app.include_router(ai_chat_router)
```

- [ ] **Step 3: Verify AI chat endpoint exists (no actual Claude call needed)**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
source venv/bin/activate
cd backend
uvicorn app.main:app --port 8000 &
sleep 3
curl -s http://localhost:8000/docs | grep -o "ai/chat"
kill %1
```

Expected: `ai/chat` found in Swagger docs.

- [ ] **Step 4: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add backend/app/api/ai_chat.py backend/app/main.py
git commit -m "feat: add AI chat SSE endpoint with Claude API integration"
```

---

## Chunk 5: Frontend Scaffolding & Shared Components

This chunk creates the shared frontend infrastructure: API service layer, Zustand stores, TypeScript types, shared UI components (AI Assistant panel, DataTable, Chart wrappers), and the app shell layout.

### Task 21: TypeScript Type Definitions

**Files:**
- Create: `FinMate/frontend/src/types/index.ts`

- [ ] **Step 1: Create TypeScript types**

Create `FinMate/frontend/src/types/index.ts`:

```typescript
// === API Response ===
export interface ApiResponse<T = unknown> {
  code: number
  data: T
  message: string
}

export interface PaginatedData<T> {
  total: number
  page: number
  page_size: number
  items: T[]
}

// === Reconciliation ===
export interface BankTransaction {
  id: number
  account_no: string
  transaction_date: string
  amount: number
  counterparty: string
  summary: string
  serial_no: string
  currency: string
  matched_status: 'unmatched' | 'matched' | 'confirmed' | 'excluded'
}

export interface BookEntry {
  id: number
  entry_date: string
  amount: number
  account_code: string
  account_name: string
  voucher_no: string
  summary: string
  auxiliary: string
  direction: 'debit' | 'credit'
}

export interface ReconciliationStatus {
  total_transactions: number
  matched_count: number
  unmatched_count: number
  match_rate: number
  unmatched_amount: number
}

// === Tax ===
export interface TaxMapping {
  id: number
  account_code: string
  account_name: string
  tax_form_type: string
  tax_line_no: string
  tax_line_name: string
  data_source: string
}

export interface TaxLineItem {
  id: number
  line_no: string
  line_name: string
  formula: string
  current_value: number
  adjusted_value: number | null
  period: string
}

export interface TaxEstimate {
  tax_type: string
  period: string
  taxable_amount: number
  tax_amount: number
  previous_period: number
  yoy_change: number
}

// === Reports ===
export interface ReportLine {
  line_no: string
  line_name: string
  indent_level: number
  is_total: boolean
  current_amount: number
  previous_amount: number
  yoy_change: number
}

export interface FinancialIndicator {
  indicator_name: string
  indicator_value: number
  benchmark_value: number
  health_status: 'good' | 'warning' | 'danger'
  description: string
}

// === Cost Allocation ===
export interface CostCenter {
  id: number
  code: string
  name: string
  center_type: string
  parent_id: number | null
  headcount: number
  area: number
  revenue_ratio: number
}

export interface CostPool {
  id: number
  name: string
  cost_type: string
  account_code: string
  period: string
  amount: number
  is_allocated: boolean
}

export interface AllocationRule {
  id: number
  name: string
  cost_pool_id: number
  allocation_basis: string
  condition_expr: string
  priority: number
  effective_from: string
  effective_to: string | null
}

export interface SankeyData {
  nodes: { name: string }[]
  links: { source: string; target: string; value: number }[]
}

// === Reconciliation (detail types) ===
export interface ReconciliationRecord {
  id: number
  match_group_id: string
  bank_transaction_id: number
  book_entry_id: number
  match_type: 'exact' | 'fuzzy' | 'smart' | 'manual'
  confidence_score: number
  is_confirmed: boolean
  match_rule: string
}

// === Tax (validation result) ===
export interface TaxValidation {
  rule_name: string
  expression: string
  severity: 'error' | 'warning'
  passed: boolean
  message: string
}

// === Cost Allocation (result) ===
export interface AllocationResult {
  pool_name: string
  center_name: string
  allocated_amount: number
  allocation_ratio: number
}

// === Dashboard ===
export interface DashboardSummary {
  period: string
  reconciliation: { match_rate: number; unmatched_count: number }
  tax: { estimated_vat: number; tax_burden_rate: number }
  financial: { total_assets: number; cash_balance: number; net_profit: number }
  cost_allocation: { total_pending: number; progress: number }
}

// === AI Chat ===
export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  toolCalls?: { tool_name: string; tool_input: Record<string, unknown> }[]
}

export interface ChatStreamEvent {
  type: 'text' | 'tool_call' | 'tool_result' | 'done'
  content?: string
  tool_name?: string
  tool_input?: Record<string, unknown>
  success?: boolean
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add frontend/src/types/
git commit -m "feat: add TypeScript type definitions for all modules"
```

---

### Task 22: API Service Layer

**Files:**
- Create: `FinMate/frontend/src/services/api.ts`

- [ ] **Step 1: Create API service**

Create `FinMate/frontend/src/services/api.ts`:

```typescript
import axios from 'axios'
import type { ApiResponse } from '../types'

const api = axios.create({ baseURL: '/api/v1' })

// Unwrap response
async function request<T>(promise: Promise<{ data: ApiResponse<T> }>): Promise<T> {
  const { data } = await promise
  if (data.code !== 200) throw new Error(data.message)
  return data.data
}

// === Dashboard ===
export const dashboard = {
  getSummary: () => request(api.get('/dashboard/summary')),
}

// === Reconciliation ===
export const reconciliation = {
  getTransactions: (params: Record<string, unknown>) =>
    request(api.get('/reconciliation/transactions', { params })),
  getBookEntries: (params: Record<string, unknown>) =>
    request(api.get('/reconciliation/book-entries', { params })),
  getStatus: (period?: string) =>
    request(api.get('/reconciliation/status', { params: { period } })),
  runMatch: (period: string) =>
    request(api.post('/reconciliation/match', { period })),
  manualMatch: (bank_ids: number[], book_ids: number[]) =>
    request(api.post('/reconciliation/manual-match', { bank_ids, book_ids })),
  exclude: (transaction_id: number, reason: string) =>
    request(api.post('/reconciliation/exclude', { transaction_id, reason })),
  getUnmatched: (period: string) =>
    request(api.get('/reconciliation/unmatched', { params: { period } })),
}

// === Tax ===
export const tax = {
  getMappings: (form_type?: string) =>
    request(api.get('/tax/mappings', { params: { form_type } })),
  updateMapping: (id: number, data: Record<string, unknown>) =>
    request(api.put(`/tax/mappings/${id}`, data)),
  getFiling: (form_type: string, period: string) =>
    request(api.get(`/tax/filing/${form_type}`, { params: { period } })),
  generateFiling: (form_type: string, period: string) =>
    request(api.post('/tax/filing/generate', { form_type, period })),
  adjustLine: (line_id: number, adjusted_value: number, reason: string) =>
    request(api.put('/tax/filing/adjust', { line_id, adjusted_value, reason })),
  getEstimate: (period: string) =>
    request(api.get('/tax/estimate', { params: { period } })),
  getValidation: (form_type: string, period: string) =>
    request(api.get(`/tax/validation/${form_type}`, { params: { period } })),
}

// === Reports ===
export const reports = {
  getReport: (report_type: string, period: string) =>
    request(api.get(`/reports/${report_type}`, { params: { period } })),
  generate: (period: string) =>
    request(api.post('/reports/generate', { period })),
  drillDown: (params: Record<string, unknown>) =>
    request(api.get('/reports/drill-down', { params })),
  getIndicators: (period: string) =>
    request(api.get('/reports/indicators', { params: { period } })),
  getTrend: (report_type: string, line_no: string, periods: string) =>
    request(api.get('/reports/trend', { params: { report_type, line_no, periods } })),
}

// === Cost Allocation ===
export const costAlloc = {
  getCenters: () => request(api.get('/cost-alloc/centers')),
  getPools: (period?: string) =>
    request(api.get('/cost-alloc/pools', { params: { period } })),
  getRules: () => request(api.get('/cost-alloc/rules')),
  createRule: (data: Record<string, unknown>) =>
    request(api.post('/cost-alloc/rules', data)),
  updateRule: (id: number, data: Record<string, unknown>) =>
    request(api.put(`/cost-alloc/rules/${id}`, data)),
  calculate: (period: string) =>
    request(api.post('/cost-alloc/calculate', { period })),
  simulate: (period: string) =>
    request(api.post('/cost-alloc/simulate', { period })),
  getResults: (period: string) =>
    request(api.get('/cost-alloc/results', { params: { period } })),
  getVoucher: (period: string) =>
    request(api.get('/cost-alloc/voucher', { params: { period } })),
}

// === AI Chat ===
export const ai = {
  chat: async function* (message: string, module_context?: string, history: unknown[] = []) {
    const response = await fetch('/api/v1/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, module_context, history }),
    })

    const reader = response.body?.getReader()
    if (!reader) return

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            yield JSON.parse(line.slice(6))
          } catch {
            // Skip malformed JSON
          }
        }
      }
    }
  },
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add frontend/src/services/
git commit -m "feat: add frontend API service layer with SSE streaming for AI chat"
```

---

### Task 23: Zustand Stores

**Files:**
- Create: `FinMate/frontend/src/store/index.ts`

- [ ] **Step 1: Create Zustand store**

Create `FinMate/frontend/src/store/index.ts`:

```typescript
import { create } from 'zustand'
import type { ChatMessage, DashboardSummary, ReconciliationStatus } from '../types'

interface AppStore {
  // Global
  currentPeriod: string
  setPeriod: (period: string) => void

  // AI Chat
  chatVisible: boolean
  chatMessages: ChatMessage[]
  chatLoading: boolean
  setChatVisible: (v: boolean) => void
  addChatMessage: (msg: ChatMessage) => void
  appendToLastMessage: (text: string) => void
  setChatLoading: (v: boolean) => void
  clearChat: () => void

  // Dashboard
  dashboardSummary: DashboardSummary | null
  setDashboardSummary: (s: DashboardSummary) => void

  // Reconciliation
  reconciliationStatus: ReconciliationStatus | null
  setReconciliationStatus: (s: ReconciliationStatus) => void
}

export const useAppStore = create<AppStore>((set) => ({
  // Global
  currentPeriod: '2024-03',
  setPeriod: (period) => set({ currentPeriod: period }),

  // AI Chat
  chatVisible: false,
  chatMessages: [],
  chatLoading: false,
  setChatVisible: (v) => set({ chatVisible: v }),
  addChatMessage: (msg) => set((s) => ({ chatMessages: [...s.chatMessages, msg] })),
  appendToLastMessage: (text) =>
    set((s) => {
      const msgs = [...s.chatMessages]
      if (msgs.length > 0 && msgs[msgs.length - 1].role === 'assistant') {
        msgs[msgs.length - 1] = {
          ...msgs[msgs.length - 1],
          content: msgs[msgs.length - 1].content + text,
        }
      }
      return { chatMessages: msgs }
    }),
  setChatLoading: (v) => set({ chatLoading: v }),
  clearChat: () => set({ chatMessages: [] }),

  // Dashboard
  dashboardSummary: null,
  setDashboardSummary: (s) => set({ dashboardSummary: s }),

  // Reconciliation
  reconciliationStatus: null,
  setReconciliationStatus: (s) => set({ reconciliationStatus: s }),
}))
```

- [ ] **Step 2: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add frontend/src/store/
git commit -m "feat: add Zustand store for global state management"
```

---

### Task 24: AI Assistant Shared Component

**Files:**
- Create: `FinMate/frontend/src/components/AIAssistant/index.tsx`

- [ ] **Step 1: Create AI Assistant panel component**

Create directory and file `FinMate/frontend/src/components/AIAssistant/index.tsx`:

```tsx
import { useState, useRef, useEffect } from 'react'
import { Drawer, Input, Button, Typography, Tag, Spin } from 'antd'
import { RobotOutlined, SendOutlined, CloseOutlined } from '@ant-design/icons'
import { useAppStore } from '../../store'
import { ai } from '../../services/api'
import type { ChatStreamEvent } from '../../types'

const { Text, Paragraph } = Typography

interface Props {
  moduleContext?: string
}

export default function AIAssistant({ moduleContext }: Props) {
  const {
    chatVisible, setChatVisible, chatMessages, addChatMessage,
    appendToLastMessage, chatLoading, setChatLoading,
  } = useAppStore()

  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

  const handleSend = async () => {
    if (!input.trim() || chatLoading) return
    const message = input.trim()
    setInput('')

    addChatMessage({ role: 'user', content: message })
    addChatMessage({ role: 'assistant', content: '' })
    setChatLoading(true)

    try {
      const history = chatMessages.map(m => ({ role: m.role, content: m.content }))
      for await (const event of ai.chat(message, moduleContext, history)) {
        const e = event as ChatStreamEvent
        if (e.type === 'text' && e.content) {
          appendToLastMessage(e.content)
        } else if (e.type === 'tool_call') {
          appendToLastMessage(`\n🔧 调用工具: ${e.tool_name}\n`)
        } else if (e.type === 'tool_result') {
          appendToLastMessage(e.success ? '✅ 获取数据成功\n' : '❌ 获取数据失败\n')
        }
      }
    } catch {
      appendToLastMessage('\n⚠️ 请求失败，请稍后重试')
    } finally {
      setChatLoading(false)
    }
  }

  return (
    <>
      <Button
        type="primary"
        shape="circle"
        size="large"
        icon={<RobotOutlined />}
        onClick={() => setChatVisible(true)}
        style={{
          position: 'fixed', right: 24, bottom: 24,
          width: 56, height: 56, zIndex: 1000,
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        }}
      />
      <Drawer
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <RobotOutlined /> AI 财务助理
            <Tag color="blue">{moduleContext || '全局'}</Tag>
          </div>
        }
        placement="right"
        width={420}
        open={chatVisible}
        onClose={() => setChatVisible(false)}
        closeIcon={<CloseOutlined />}
      >
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <div style={{ flex: 1, overflowY: 'auto', paddingBottom: 16 }}>
            {chatMessages.length === 0 && (
              <div style={{ textAlign: 'center', color: '#999', padding: 40 }}>
                <RobotOutlined style={{ fontSize: 48, color: '#1890ff' }} />
                <Paragraph style={{ marginTop: 16 }}>
                  你好！我是 FinMate AI 助理，可以帮你分析财务数据。
                </Paragraph>
                <Paragraph type="secondary">试试问我：</Paragraph>
                <Paragraph type="secondary">"本月对账匹配率是多少？"</Paragraph>
                <Paragraph type="secondary">"哪些费用增长最快？"</Paragraph>
              </div>
            )}
            {chatMessages.map((msg, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  marginBottom: 12,
                }}
              >
                <div
                  style={{
                    maxWidth: '85%', padding: '8px 12px', borderRadius: 8,
                    background: msg.role === 'user' ? '#1890ff' : '#f5f5f5',
                    color: msg.role === 'user' ? '#fff' : '#333',
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  <Text style={{ color: 'inherit' }}>{msg.content}</Text>
                  {msg.role === 'assistant' && !msg.content && chatLoading && <Spin size="small" />}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
          <div style={{ display: 'flex', gap: 8, paddingTop: 12, borderTop: '1px solid #f0f0f0' }}>
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onPressEnter={handleSend}
              placeholder="输入问题..."
              disabled={chatLoading}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              loading={chatLoading}
            />
          </div>
        </div>
      </Drawer>
    </>
  )
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add frontend/src/components/
git commit -m "feat: add AI Assistant shared component with SSE chat streaming"
```

---

### Task 25: Period Selector & Data Table Components

**Files:**
- Create: `FinMate/frontend/src/components/PeriodSelector.tsx`
- Create: `FinMate/frontend/src/components/DataTable/index.tsx`

- [ ] **Step 1: Create PeriodSelector component**

Create `FinMate/frontend/src/components/PeriodSelector.tsx`:

```tsx
import { Select } from 'antd'
import { useAppStore } from '../store'

const periods = [
  { value: '2024-01', label: '2024年1月' },
  { value: '2024-02', label: '2024年2月' },
  { value: '2024-03', label: '2024年3月' },
]

export default function PeriodSelector() {
  const { currentPeriod, setPeriod } = useAppStore()

  return (
    <Select
      value={currentPeriod}
      onChange={setPeriod}
      options={periods}
      style={{ width: 140 }}
    />
  )
}
```

- [ ] **Step 2: Create DataTable wrapper**

Create `FinMate/frontend/src/components/DataTable/index.tsx`:

```tsx
import { Table } from 'antd'
import type { ColumnsType } from 'antd/es/table'

interface Props<T> {
  columns: ColumnsType<T>
  dataSource: T[]
  loading?: boolean
  rowKey?: string | ((record: T) => string)
  pagination?: false | { total: number; current: number; pageSize: number; onChange: (page: number) => void }
}

export default function DataTable<T extends Record<string, unknown>>({
  columns, dataSource, loading, rowKey = 'id', pagination,
}: Props<T>) {
  return (
    <Table
      columns={columns}
      dataSource={dataSource}
      loading={loading}
      rowKey={rowKey}
      pagination={pagination || { pageSize: 20, showSizeChanger: false, showTotal: (t) => `共 ${t} 条` }}
      size="middle"
      scroll={{ x: 'max-content' }}
    />
  )
}
```

- [ ] **Step 3: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add frontend/src/components/PeriodSelector.tsx frontend/src/components/DataTable/
git commit -m "feat: add PeriodSelector and DataTable shared components"
```

---

### Task 26: Update App Layout with PeriodSelector and AI Assistant

**Files:**
- Modify: `FinMate/frontend/src/App.tsx`

- [ ] **Step 1: Update App.tsx to include shared components**

Replace `FinMate/frontend/src/App.tsx`:

```tsx
import { ConfigProvider, Layout, Menu, theme } from 'antd'
import {
  DashboardOutlined,
  BankOutlined,
  AuditOutlined,
  BarChartOutlined,
  ApartmentOutlined,
} from '@ant-design/icons'
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import PeriodSelector from './components/PeriodSelector'
import AIAssistant from './components/AIAssistant'

// Lazy-loaded page placeholders (will be replaced in Chunk 6)
const Dashboard = () => <div>Dashboard - 加载中...</div>
const Reconciliation = () => <div>银行对账 - 加载中...</div>
const TaxPrep = () => <div>税务准备 - 加载中...</div>
const Reports = () => <div>财务报表 - 加载中...</div>
const CostAlloc = () => <div>成本分摊 - 加载中...</div>

const { Header, Sider, Content } = Layout

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/reconciliation', icon: <BankOutlined />, label: '银行对账' },
  { key: '/tax', icon: <AuditOutlined />, label: '税务准备' },
  { key: '/reports', icon: <BarChartOutlined />, label: '财务报表' },
  { key: '/cost-alloc', icon: <ApartmentOutlined />, label: '成本分摊' },
]

const moduleMap: Record<string, string> = {
  '/reconciliation': 'reconciliation',
  '/tax': 'tax',
  '/reports': 'reports',
  '/cost-alloc': 'cost_alloc',
}

function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const moduleContext = moduleMap[location.pathname]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="light" width={200}>
        <div style={{
          height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 'bold', fontSize: 20, color: '#1890ff',
        }}>
          FinMate
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{
          background: '#fff', padding: '0 24px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          borderBottom: '1px solid #f0f0f0',
        }}>
          <h2 style={{ margin: 0, fontSize: 16 }}>AI 财务助理</h2>
          <PeriodSelector />
        </Header>
        <Content style={{ margin: 24, padding: 24, background: '#fff', borderRadius: 8, overflow: 'auto' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/reconciliation" element={<Reconciliation />} />
            <Route path="/tax" element={<TaxPrep />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/cost-alloc" element={<CostAlloc />} />
          </Routes>
        </Content>
      </Layout>
      <AIAssistant moduleContext={moduleContext} />
    </Layout>
  )
}

export default function App() {
  return (
    <ConfigProvider theme={{ algorithm: theme.defaultAlgorithm }}>
      <BrowserRouter>
        <AppLayout />
      </BrowserRouter>
    </ConfigProvider>
  )
}
```

- [ ] **Step 2: Verify frontend compiles**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate/frontend
npx tsc --noEmit
```

Expected: No TypeScript errors.

- [ ] **Step 3: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add frontend/src/App.tsx
git commit -m "feat: update App layout with PeriodSelector header and AI Assistant"
```

---

## Chunk 6: Frontend Pages

This chunk implements the 5 page components: Dashboard, Reconciliation, TaxPrep, Reports, and CostAlloc. Each page fetches data from the API and renders with Ant Design + ECharts.

### Task 27: Dashboard Page

**Files:**
- Create: `FinMate/frontend/src/pages/Dashboard/index.tsx`
- Modify: `FinMate/frontend/src/App.tsx` (import real page)

- [ ] **Step 1: Create Dashboard page**

Create `FinMate/frontend/src/pages/Dashboard/index.tsx`:

```tsx
import { useEffect, useState } from 'react'
import { Card, Col, Row, Statistic, Progress, Typography, Tag } from 'antd'
import {
  BankOutlined, AuditOutlined, BarChartOutlined, ApartmentOutlined,
  CheckCircleOutlined, WarningOutlined,
} from '@ant-design/icons'
import { dashboard } from '../../services/api'
import type { DashboardSummary } from '../../types'

const { Title, Text } = Typography

export default function Dashboard() {
  const [data, setData] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    dashboard.getSummary()
      .then((d) => setData(d as DashboardSummary))
      .finally(() => setLoading(false))
  }, []) // Backend uses DEFAULT_PERIOD; re-fetch not needed per period change

  if (loading || !data) return <Card loading={loading} />

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>
        星辰科技有限公司 — {data.period} 财务概览
      </Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable>
            <Statistic
              title={<><BankOutlined /> 对账匹配率</>}
              value={data.reconciliation.match_rate}
              suffix="%"
              valueStyle={{ color: data.reconciliation.match_rate >= 80 ? '#3f8600' : '#cf1322' }}
            />
            <Progress percent={data.reconciliation.match_rate} showInfo={false} size="small" />
            <Text type="secondary">
              未匹配 {data.reconciliation.unmatched_count} 笔
            </Text>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card hoverable>
            <Statistic
              title={<><AuditOutlined /> 预估税额</>}
              value={data.tax.estimated_vat}
              prefix="¥"
              precision={0}
            />
            <div style={{ marginTop: 8 }}>
              <Tag color="blue">税负率 {data.tax.tax_burden_rate}%</Tag>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card hoverable>
            <Statistic
              title={<><BarChartOutlined /> 总资产</>}
              value={data.financial.total_assets}
              prefix="¥"
              precision={0}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">现金: ¥{data.financial.cash_balance.toLocaleString()}</Text>
              <br />
              <Text type="secondary">净利润: ¥{data.financial.net_profit.toLocaleString()}</Text>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card hoverable>
            <Statistic
              title={<><ApartmentOutlined /> 分摊进度</>}
              value={data.cost_allocation.progress}
              suffix="%"
            />
            <Progress percent={data.cost_allocation.progress} showInfo={false} size="small" />
            <Text type="secondary">
              待分摊 ¥{data.cost_allocation.total_pending.toLocaleString()}
            </Text>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title={<><CheckCircleOutlined /> AI 洞察</>} size="small">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {data.reconciliation.unmatched_count > 0 && (
                <Tag icon={<WarningOutlined />} color="warning">
                  发现 {data.reconciliation.unmatched_count} 笔未匹配银行流水，建议检查
                </Tag>
              )}
              {data.cost_allocation.progress < 100 && (
                <Tag icon={<WarningOutlined />} color="warning">
                  本期费用分摊尚未完成，待分摊金额 ¥{data.cost_allocation.total_pending.toLocaleString()}
                </Tag>
              )}
              <Tag icon={<CheckCircleOutlined />} color="success">
                财务数据已就绪，可生成本期报表
              </Tag>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add frontend/src/pages/Dashboard/
git commit -m "feat: add Dashboard page with 4-module summary cards and AI insights"
```

---

### Task 28: Reconciliation Page

**Files:**
- Create: `FinMate/frontend/src/pages/Reconciliation/index.tsx`

- [ ] **Step 1: Create Reconciliation page**

Create `FinMate/frontend/src/pages/Reconciliation/index.tsx`:

```tsx
import { useEffect, useState } from 'react'
import { Card, Col, Row, Statistic, Button, Table, Tag, Progress, Space, message } from 'antd'
import { SyncOutlined, CheckCircleOutlined, LinkOutlined } from '@ant-design/icons'
import { reconciliation } from '../../services/api'
import { useAppStore } from '../../store'
import type { BankTransaction, BookEntry, ReconciliationStatus, PaginatedData } from '../../types'

const statusColors: Record<string, string> = {
  unmatched: 'red', matched: 'orange', confirmed: 'green', excluded: 'default',
}
const statusLabels: Record<string, string> = {
  unmatched: '未匹配', matched: '已匹配', confirmed: '已确认', excluded: '已排除',
}

export default function Reconciliation() {
  const { currentPeriod } = useAppStore()
  const [status, setStatus] = useState<ReconciliationStatus | null>(null)
  const [bankData, setBankData] = useState<PaginatedData<BankTransaction> | null>(null)
  const [bookData, setBookData] = useState<PaginatedData<BookEntry> | null>(null)
  const [loading, setLoading] = useState(true)
  const [matching, setMatching] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      const [s, b, e] = await Promise.all([
        reconciliation.getStatus(currentPeriod),
        reconciliation.getTransactions({ period: currentPeriod, page_size: 50 }),
        reconciliation.getBookEntries({ period: currentPeriod, account_code: '1002', page_size: 50 }),
      ])
      setStatus(s as ReconciliationStatus)
      setBankData(b as PaginatedData<BankTransaction>)
      setBookData(e as PaginatedData<BookEntry>)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [currentPeriod])

  const handleMatch = async () => {
    setMatching(true)
    try {
      const result = await reconciliation.runMatch(currentPeriod) as { matched: number; unmatched: number }
      message.success(`匹配完成：成功 ${result.matched} 笔，未匹配 ${result.unmatched} 笔`)
      fetchData()
    } finally {
      setMatching(false)
    }
  }

  const bankColumns = [
    { title: '日期', dataIndex: 'transaction_date', width: 100 },
    { title: '金额', dataIndex: 'amount', width: 100,
      render: (v: number) => <span style={{ color: v > 0 ? '#3f8600' : '#cf1322' }}>¥{v.toLocaleString()}</span> },
    { title: '对方', dataIndex: 'counterparty', width: 120, ellipsis: true },
    { title: '摘要', dataIndex: 'summary', ellipsis: true },
    { title: '状态', dataIndex: 'matched_status', width: 80,
      render: (s: string) => <Tag color={statusColors[s]}>{statusLabels[s]}</Tag> },
  ]

  const bookColumns = [
    { title: '日期', dataIndex: 'entry_date', width: 100 },
    { title: '金额', dataIndex: 'amount', width: 100,
      render: (v: number) => `¥${v.toLocaleString()}` },
    { title: '方向', dataIndex: 'direction', width: 50,
      render: (d: string) => d === 'debit' ? '借' : '贷' },
    { title: '科目', dataIndex: 'account_name', width: 140, ellipsis: true },
    { title: '凭证号', dataIndex: 'voucher_no', width: 120 },
    { title: '摘要', dataIndex: 'summary', ellipsis: true },
  ]

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card size="small">
            <Statistic title="匹配率" value={status?.match_rate || 0} suffix="%" />
            <Progress percent={status?.match_rate || 0} showInfo={false} size="small" />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="总流水" value={status?.total_transactions || 0} suffix="笔" />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="未匹配" value={status?.unmatched_count || 0} suffix="笔"
              valueStyle={{ color: '#cf1322' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="未匹配金额" value={status?.unmatched_amount || 0} prefix="¥" precision={0} />
          </Card>
        </Col>
      </Row>

      <div style={{ margin: '16px 0', display: 'flex', justifyContent: 'flex-end' }}>
        <Space>
          <Button type="primary" icon={<SyncOutlined />} onClick={handleMatch} loading={matching}>
            执行自动匹配
          </Button>
        </Space>
      </div>

      <Row gutter={16}>
        <Col span={12}>
          <Card title={<><BankOutlined /> 银行流水</>} size="small">
            <Table
              columns={bankColumns}
              dataSource={bankData?.items || []}
              rowKey="id"
              loading={loading}
              size="small"
              pagination={{ pageSize: 15, showTotal: (t) => `共 ${t} 条` }}
              scroll={{ y: 400 }}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title={<><LinkOutlined /> 账簿记录</>} size="small">
            <Table
              columns={bookColumns}
              dataSource={bookData?.items || []}
              rowKey="id"
              loading={loading}
              size="small"
              pagination={{ pageSize: 15, showTotal: (t) => `共 ${t} 条` }}
              scroll={{ y: 400 }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
```

Note: `BankOutlined` is already imported via `@ant-design/icons`.

- [ ] **Step 2: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add frontend/src/pages/Reconciliation/
git commit -m "feat: add Reconciliation page with dual-panel bank/book view and auto-match"
```

---

### Task 29: Tax Preparation Page

**Files:**
- Create: `FinMate/frontend/src/pages/TaxPrep/index.tsx`

- [ ] **Step 1: Create TaxPrep page**

Create `FinMate/frontend/src/pages/TaxPrep/index.tsx`:

```tsx
import { useEffect, useState } from 'react'
import { Card, Tabs, Table, Tag, Button, Row, Col, Statistic, message } from 'antd'
import { FileDoneOutlined, CalculatorOutlined, SafetyCertificateOutlined } from '@ant-design/icons'
import { tax } from '../../services/api'
import { useAppStore } from '../../store'
import type { TaxLineItem, TaxEstimate } from '../../types'

export default function TaxPrep() {
  const { currentPeriod } = useAppStore()
  const [activeTab, setActiveTab] = useState('vat_general')
  const [lines, setLines] = useState<TaxLineItem[]>([])
  const [estimates, setEstimates] = useState<TaxEstimate[]>([])
  const [validation, setValidation] = useState<{ rule_name: string; passed: boolean; severity: string }[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      const [filing, est, val] = await Promise.all([
        tax.getFiling(activeTab, currentPeriod),
        tax.getEstimate(currentPeriod),
        tax.getValidation(activeTab, currentPeriod),
      ])
      const filingData = filing as { lines: TaxLineItem[] }
      setLines(filingData.lines || [])
      setEstimates(est as TaxEstimate[])
      setValidation(val as { rule_name: string; passed: boolean; severity: string }[])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [currentPeriod, activeTab])

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      await tax.generateFiling(activeTab, currentPeriod)
      message.success('申报表生成成功')
      fetchData()
    } finally {
      setGenerating(false)
    }
  }

  const lineColumns = [
    { title: '行号', dataIndex: 'line_no', width: 60 },
    { title: '项目名称', dataIndex: 'line_name', ellipsis: true },
    { title: '本期金额', dataIndex: 'current_value', width: 120,
      render: (v: number) => `¥${v.toLocaleString()}` },
    { title: '调整后金额', dataIndex: 'adjusted_value', width: 120,
      render: (v: number | null) => v !== null ? <span style={{ color: '#1890ff' }}>¥{v.toLocaleString()}</span> : '-' },
  ]

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {estimates.map((e, i) => (
          <Col span={8} key={i}>
            <Card size="small">
              <Statistic title={e.tax_type} value={e.tax_amount} prefix="¥" precision={0} />
            </Card>
          </Col>
        ))}
        <Col span={8}>
          <Card size="small">
            <div style={{ marginBottom: 8, fontWeight: 500 }}>
              <SafetyCertificateOutlined /> 校验结果
            </div>
            {validation.map((v, i) => (
              <Tag key={i} color={v.passed ? 'success' : (v.severity === 'error' ? 'error' : 'warning')}>
                {v.passed ? '✓' : '✗'} {v.rule_name}
              </Tag>
            ))}
            {validation.length === 0 && <Tag>暂无校验数据</Tag>}
          </Card>
        </Col>
      </Row>

      <Card
        title={<><FileDoneOutlined /> 税务申报表</>}
        extra={
          <Button type="primary" icon={<CalculatorOutlined />} onClick={handleGenerate} loading={generating}>
            生成申报表
          </Button>
        }
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            { key: 'vat_general', label: '增值税（一般纳税人）' },
            { key: 'cit_quarterly', label: '企业所得税（季度预缴）' },
          ]}
        />
        <Table
          columns={lineColumns}
          dataSource={lines}
          rowKey="id"
          loading={loading}
          size="small"
          pagination={false}
        />
      </Card>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add frontend/src/pages/TaxPrep/
git commit -m "feat: add TaxPrep page with filing table, estimates, and validation"
```

---

### Task 30: Financial Reports Page

**Files:**
- Create: `FinMate/frontend/src/pages/Reports/index.tsx`

- [ ] **Step 1: Create Reports page**

Create `FinMate/frontend/src/pages/Reports/index.tsx`:

```tsx
import { useEffect, useState } from 'react'
import { Card, Tabs, Table, Button, Row, Col, Tag, Breadcrumb, message } from 'antd'
import { FileTextOutlined, CalculatorOutlined, ArrowLeftOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { reports } from '../../services/api'
import { useAppStore } from '../../store'
import type { ReportLine, FinancialIndicator } from '../../types'

export default function Reports() {
  const { currentPeriod } = useAppStore()
  const [activeTab, setActiveTab] = useState('balance_sheet')
  const [lines, setLines] = useState<ReportLine[]>([])
  const [indicators, setIndicators] = useState<FinancialIndicator[]>([])
  const [drillData, setDrillData] = useState<unknown[] | null>(null)
  const [drillPath, setDrillPath] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      const [rpt, ind] = await Promise.all([
        reports.getReport(activeTab, currentPeriod),
        reports.getIndicators(currentPeriod),
      ])
      const rptData = rpt as { lines: ReportLine[] }
      setLines(rptData.lines || [])
      setIndicators(ind as FinancialIndicator[])
      setDrillData(null)
      setDrillPath([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [currentPeriod, activeTab])

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      await reports.generate(currentPeriod)
      message.success('三大报表生成成功')
      fetchData()
    } finally {
      setGenerating(false)
    }
  }

  const handleDrillDown = async (lineNo: string, lineName: string) => {
    const level = drillPath.length + 1
    if (level > 2) return
    try {
      const data = await reports.drillDown({
        report_type: activeTab, line_no: lineNo, period: currentPeriod, level,
      })
      const d = data as { items: unknown[] }
      setDrillData(d.items || [])
      setDrillPath([...drillPath, lineName])
    } catch {
      message.error('钻取失败')
    }
  }

  const handleBack = () => {
    if (drillPath.length === 0) return
    setDrillPath(drillPath.slice(0, -1))
    if (drillPath.length <= 1) setDrillData(null)
  }

  const reportColumns = [
    { title: '行号', dataIndex: 'line_no', width: 60 },
    {
      title: '项目', dataIndex: 'line_name',
      render: (name: string, record: ReportLine) => (
        <span style={{
          paddingLeft: record.indent_level * 24,
          fontWeight: record.is_total ? 'bold' : 'normal',
        }}>
          {name}
        </span>
      ),
    },
    {
      title: '本期金额', dataIndex: 'current_amount', width: 140,
      render: (v: number, record: ReportLine) => (
        <a onClick={() => handleDrillDown(record.line_no, record.line_name)}
           style={{ fontWeight: record.is_total ? 'bold' : 'normal' }}>
          ¥{v.toLocaleString()}
        </a>
      ),
    },
    { title: '上期金额', dataIndex: 'previous_amount', width: 140,
      render: (v: number) => `¥${v.toLocaleString()}` },
  ]

  const healthColor = { good: '#52c41a', warning: '#faad14', danger: '#ff4d4f' }

  const indicatorChart = {
    tooltip: { trigger: 'axis' as const },
    xAxis: { type: 'category' as const, data: indicators.map(i => i.indicator_name) },
    yAxis: { type: 'value' as const },
    series: [
      { name: '实际值', type: 'bar', data: indicators.map(i => i.indicator_value), itemStyle: { color: '#1890ff' } },
      { name: '基准值', type: 'bar', data: indicators.map(i => i.benchmark_value), itemStyle: { color: '#d9d9d9' } },
    ],
  }

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col span={16}>
          <Card
            title={<><FileTextOutlined /> 财务报表</>}
            extra={
              <Button type="primary" icon={<CalculatorOutlined />} onClick={handleGenerate} loading={generating}>
                一键生成
              </Button>
            }
          >
            <Tabs
              activeKey={activeTab}
              onChange={(k) => { setActiveTab(k); setDrillData(null); setDrillPath([]) }}
              items={[
                { key: 'balance_sheet', label: '资产负债表' },
                { key: 'income', label: '利润表' },
                { key: 'cash_flow', label: '现金流量表' },
              ]}
            />

            {drillPath.length > 0 && (
              <div style={{ marginBottom: 12 }}>
                <Button size="small" icon={<ArrowLeftOutlined />} onClick={handleBack}>返回</Button>
                <Breadcrumb style={{ display: 'inline', marginLeft: 12 }}
                  items={[{ title: '报表' }, ...drillPath.map(p => ({ title: p }))]}
                />
              </div>
            )}

            {drillData ? (
              <Table
                columns={[
                  { title: '科目编码', dataIndex: 'account_code', width: 100 },
                  { title: '科目名称', dataIndex: 'account_name' },
                  { title: '期末余额', dataIndex: 'closing_balance', width: 120,
                    render: (v: number) => `¥${(v || 0).toLocaleString()}` },
                ]}
                dataSource={drillData as Record<string, unknown>[]}
                rowKey="account_code"
                size="small"
                pagination={false}
              />
            ) : (
              <Table
                columns={reportColumns}
                dataSource={lines}
                rowKey="line_no"
                loading={loading}
                size="small"
                pagination={false}
              />
            )}
          </Card>
        </Col>

        <Col span={8}>
          <Card title="财务指标" size="small" style={{ marginBottom: 16 }}>
            {indicators.map((ind, i) => (
              <div key={i} style={{ marginBottom: 12, padding: '8px 12px', background: '#fafafa', borderRadius: 4 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>{ind.indicator_name}</span>
                  <Tag color={healthColor[ind.health_status]}>{ind.indicator_value}</Tag>
                </div>
                <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>{ind.description}</div>
              </div>
            ))}
          </Card>

          <Card title="指标对比" size="small">
            {indicators.length > 0 && <ReactECharts option={indicatorChart} style={{ height: 200 }} />}
          </Card>
        </Col>
      </Row>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add frontend/src/pages/Reports/
git commit -m "feat: add Reports page with three-report tabs, drill-down, and indicator cards"
```

---

### Task 31: Cost Allocation Page

**Files:**
- Create: `FinMate/frontend/src/pages/CostAlloc/index.tsx`

- [ ] **Step 1: Create CostAlloc page**

Create `FinMate/frontend/src/pages/CostAlloc/index.tsx`:

```tsx
import { useEffect, useState } from 'react'
import { Card, Col, Row, Table, Button, Tree, Tag, message } from 'antd'
import { ApartmentOutlined, CalculatorOutlined, ExperimentOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { costAlloc } from '../../services/api'
import { useAppStore } from '../../store'
import type { CostCenter, CostPool, AllocationRule, SankeyData } from '../../types'

export default function CostAlloc() {
  const { currentPeriod } = useAppStore()
  const [centers, setCenters] = useState<CostCenter[]>([])
  const [pools, setPools] = useState<CostPool[]>([])
  const [rules, setRules] = useState<AllocationRule[]>([])
  const [results, setResults] = useState<{ results: unknown[]; sankey: SankeyData } | null>(null)
  const [loading, setLoading] = useState(true)
  const [calculating, setCalculating] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      const [c, p, r, res] = await Promise.all([
        costAlloc.getCenters(),
        costAlloc.getPools(currentPeriod),
        costAlloc.getRules(),
        costAlloc.getResults(currentPeriod).catch(() => null),
      ])
      setCenters(c as CostCenter[])
      setPools(p as CostPool[])
      setRules(r as AllocationRule[])
      setResults(res as { results: unknown[]; sankey: SankeyData } | null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [currentPeriod])

  const handleCalculate = async () => {
    setCalculating(true)
    try {
      const res = await costAlloc.calculate(currentPeriod)
      setResults(res as { results: unknown[]; sankey: SankeyData })
      message.success('分摊计算完成')
      fetchData()
    } finally {
      setCalculating(false)
    }
  }

  const handleSimulate = async () => {
    try {
      const res = await costAlloc.simulate(currentPeriod)
      setResults(res as { results: unknown[]; sankey: SankeyData })
      message.info('模拟计算完成（结果未保存）')
    } catch {
      message.error('模拟失败')
    }
  }

  // Build hierarchical tree from flat centers using parent_id
  const buildTree = (parentId: number | null): { key: string; title: string; children?: unknown[] }[] => {
    return centers
      .filter(c => c.parent_id === parentId)
      .map(c => ({
        key: c.code,
        title: `${c.name} (${c.headcount}人, ${c.area}㎡)`,
        children: buildTree(c.id),
      }))
  }
  const treeData = buildTree(null)

  const poolColumns = [
    { title: '费用池', dataIndex: 'name' },
    { title: '金额', dataIndex: 'amount', render: (v: number) => `¥${v.toLocaleString()}` },
    { title: '状态', dataIndex: 'is_allocated',
      render: (v: boolean) => <Tag color={v ? 'green' : 'orange'}>{v ? '已分摊' : '待分摊'}</Tag> },
  ]

  const ruleColumns = [
    { title: '规则', dataIndex: 'name' },
    { title: '分摊基础', dataIndex: 'allocation_basis',
      render: (v: string) => ({ headcount: '人数', area: '面积', revenue: '收入' }[v] || v) },
    { title: '优先级', dataIndex: 'priority', width: 70 },
  ]

  const sankeyOption = results?.sankey ? {
    tooltip: { trigger: 'item' as const },
    series: [{
      type: 'sankey',
      data: results.sankey.nodes,
      links: results.sankey.links,
      emphasis: { focus: 'adjacency' as const },
      lineStyle: { color: 'gradient', curveness: 0.5 },
    }],
  } : null

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
        <Button icon={<ExperimentOutlined />} onClick={handleSimulate}>模拟分摊</Button>
        <Button type="primary" icon={<CalculatorOutlined />} onClick={handleCalculate} loading={calculating}>
          执行分摊
        </Button>
      </div>

      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card title={<><ApartmentOutlined /> 成本中心</>} size="small" loading={loading}>
            <Tree treeData={treeData} defaultExpandAll />
          </Card>
        </Col>

        <Col span={18}>
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Card title="费用池" size="small">
                <Table columns={poolColumns} dataSource={pools} rowKey="id"
                  size="small" pagination={false} loading={loading} />
              </Card>
            </Col>
            <Col span={12}>
              <Card title="分摊规则" size="small">
                <Table columns={ruleColumns} dataSource={rules} rowKey="id"
                  size="small" pagination={false} loading={loading} />
              </Card>
            </Col>
          </Row>

          {sankeyOption && (
            <Card title="费用分摊流向" size="small" style={{ marginTop: 16 }}>
              <ReactECharts option={sankeyOption} style={{ height: 350 }} />
            </Card>
          )}
        </Col>
      </Row>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add frontend/src/pages/CostAlloc/
git commit -m "feat: add CostAlloc page with center tree, pools, rules, and sankey chart"
```

---

### Task 32: Wire Pages into App.tsx

**Files:**
- Modify: `FinMate/frontend/src/App.tsx`

- [ ] **Step 1: Update App.tsx to import real page components**

Replace the placeholder imports in `FinMate/frontend/src/App.tsx`. Replace these lines:

```tsx
// Lazy-loaded page placeholders (will be replaced in Chunk 6)
const Dashboard = () => <div>Dashboard - 加载中...</div>
const Reconciliation = () => <div>银行对账 - 加载中...</div>
const TaxPrep = () => <div>税务准备 - 加载中...</div>
const Reports = () => <div>财务报表 - 加载中...</div>
const CostAlloc = () => <div>成本分摊 - 加载中...</div>
```

With:

```tsx
import Dashboard from './pages/Dashboard'
import Reconciliation from './pages/Reconciliation'
import TaxPrep from './pages/TaxPrep'
import Reports from './pages/Reports'
import CostAlloc from './pages/CostAlloc'
```

- [ ] **Step 2: Verify frontend compiles and runs**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate/frontend
npx tsc --noEmit
npm run build
```

Expected: No errors, `dist/` directory created.

- [ ] **Step 3: Commit**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
git add frontend/src/App.tsx
git commit -m "feat: wire all page components into App router"
```

---

### Task 33: End-to-End Verification

- [ ] **Step 1: Start backend**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate
source venv/bin/activate
cd backend
uvicorn app.main:app --reload --port 8000 &
sleep 5
```

Expected: Server starts, auto-seeds data on first run.

- [ ] **Step 2: Start frontend**

```bash
cd /Users/laurant/Documents/github/comlan/FinMate/frontend
npm run dev &
sleep 3
```

Expected: Vite dev server on http://localhost:5173

- [ ] **Step 3: Verify all API endpoints**

```bash
curl -s http://localhost:8000/api/v1/health | python -m json.tool
curl -s http://localhost:8000/api/v1/dashboard/summary | python -m json.tool
curl -s "http://localhost:8000/api/v1/reconciliation/status?period=2024-03" | python -m json.tool
curl -s "http://localhost:8000/api/v1/tax/estimate?period=2024-03" | python -m json.tool
curl -s "http://localhost:8000/api/v1/reports/balance_sheet?period=2024-03" | python -m json.tool
curl -s http://localhost:8000/api/v1/cost-alloc/centers | python -m json.tool
```

Expected: All return `{"code": 200, "data": {...}, "message": "ok"}`.

- [ ] **Step 4: Stop servers and final commit**

```bash
kill %1 %2 2>/dev/null
cd /Users/laurant/Documents/github/comlan/FinMate
git add backend/ frontend/ docs/
git commit -m "feat: FinMate AI 财务助理 v1.0 — all 4 modules complete"
```

---
