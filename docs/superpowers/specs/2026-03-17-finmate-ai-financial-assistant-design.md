# FinMate - AI 财务助理 设计文档

## 1. 项目概述

### 1.1 背景与目标

构建一个面向客户/投资人演示的 AI 财务助理产品原型（FinMate），展示 AI + Agent 在财务场景中的智能化能力。财务系统对接采用 Mock 数据，确保演示效果逼真流畅。

### 1.2 核心功能范围

1. **银行对账自动化** — 多级智能匹配 + AI 异常分析
2. **税务数据准备** — 科目映射 + 申报表自动生成 + 智能校验
3. **财务报表生成** — 三大报表一键生成 + 三级钻取 + AI 财务分析
4. **成本分摊计算** — 规则引擎 + 可视化分摊流向 + AI 优化建议

### 1.3 目标受众

客户/投资人演示，需要精美 UI、逼真 Mock 数据、流畅交互体验。

---

## 2. 技术架构

### 2.1 架构概览

单体全功能架构：React SPA + FastAPI 单服务 + SQLite + Claude API

```
┌─────────────────────────────────────────────────┐
│                  React SPA                       │
│        (Vite + Ant Design 5 + ECharts)          │
└─────────────────┬───────────────────────────────┘
                  │ REST API
┌─────────────────▼───────────────────────────────┐
│                 FastAPI                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ API路由  │ │ 业务服务 │ │   AI Agent 层    │ │
│  │ (Router) │ │(Service) │ │(Claude tool_use) │ │
│  └────┬─────┘ └────┬─────┘ └───────┬──────────┘ │
│       │             │               │             │
│  ┌────▼─────────────▼───────────────▼──────────┐ │
│  │          SQLAlchemy + SQLite                  │ │
│  └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

### 2.2 技术选型

| 层 | 技术 | 说明 |
|---|---|---|
| 前端框架 | React 18 + Vite | 快速开发，HMR |
| UI 组件库 | Ant Design 5 | 中后台风格，天然适合财务系统 |
| 图表 | ECharts 5 | 桑基图、旭日图、趋势图等 |
| 状态管理 | Zustand | 轻量、简洁 |
| 后端框架 | FastAPI | 异步高性能、自动 API 文档 |
| ORM | SQLAlchemy 2.0 | 类型安全、异步支持 |
| 数据库 | SQLite | 零配置、演示友好 |
| AI | Anthropic Claude API (tool_use) | Agent 多步推理 |
| Python 环境 | venv (项目根目录) | 虚拟环境隔离 |

### 2.3 项目结构

```
FinMate/
├── venv/                          # Python 虚拟环境
├── frontend/                      # React 前端
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard/         # 首页仪表盘
│   │   │   ├── Reconciliation/    # 银行对账自动化
│   │   │   ├── TaxPrep/           # 税务数据准备
│   │   │   ├── Reports/           # 财务报表生成
│   │   │   └── CostAlloc/         # 成本分摊计算
│   │   ├── components/            # 共享 UI 组件
│   │   │   ├── AIAssistant/       # AI 助手面板（全局共享）
│   │   │   ├── DataTable/         # 通用数据表格
│   │   │   └── Charts/            # 图表封装
│   │   ├── services/              # API 调用层
│   │   ├── store/                 # Zustand 状态管理
│   │   ├── types/                 # TypeScript 类型定义
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                       # Python 后端
│   ├── app/
│   │   ├── api/                   # 路由层
│   │   │   ├── reconciliation.py  # 银行对账 API
│   │   │   ├── tax.py             # 税务数据 API
│   │   │   ├── reports.py         # 财务报表 API
│   │   │   ├── cost_alloc.py      # 成本分摊 API
│   │   │   └── ai_chat.py         # AI 对话 API
│   │   ├── models/                # SQLAlchemy 数据模型
│   │   │   ├── base.py
│   │   │   ├── reconciliation.py
│   │   │   ├── tax.py
│   │   │   ├── reports.py
│   │   │   └── cost_alloc.py
│   │   ├── services/              # 业务逻辑层
│   │   │   ├── reconciliation_service.py
│   │   │   ├── tax_service.py
│   │   │   ├── report_service.py
│   │   │   └── cost_alloc_service.py
│   │   ├── agent/                 # AI Agent 编排
│   │   │   ├── agent.py           # Agent 主逻辑（Claude tool_use）
│   │   │   └── tools.py           # Agent 工具定义
│   │   ├── mock/                  # Mock 数据
│   │   │   └── seed.py            # 数据库种子脚本
│   │   ├── database.py            # 数据库连接配置
│   │   └── main.py                # FastAPI 入口
│   └── requirements.txt
│
└── docs/
    └── superpowers/
        └── specs/
```

### 2.4 环境配置

```
# Python 版本
Python >= 3.11

# Node 版本
Node.js >= 18

# 环境变量 (.env)
ANTHROPIC_API_KEY=sk-ant-xxx        # Claude API 密钥
DATABASE_URL=sqlite:///./finmate.db  # 数据库路径
CORS_ORIGINS=http://localhost:5173   # 前端地址
```

### 2.5 共享数据模型

`AccountBalance` 和 `BookEntry` 是跨模块共享模型，放在 `backend/app/models/base.py`：
- **AccountBalance**：Reports（报表生成）和 TaxPrep（税务取数）共用
- **BookEntry**：Reconciliation（对账）和 Reports（钻取到凭证）共用
- AccountBalance 由 seed 脚本从 BookEntry 汇总生成，保证数据一致性

### 2.6 统一期间格式

所有模块统一使用 `YYYY-MM` 格式（如 `2024-03`）。季度/年度数据通过聚合月度数据生成，不单独存储。

### 2.7 会计科目体系

Mock 数据采用**小企业会计准则**科目体系，预置约60个常用科目：

| 类别 | 编码范围 | 示例科目 |
|------|----------|----------|
| 资产 | 1001-1901 | 库存现金、银行存款、应收账款、存货、固定资产 |
| 负债 | 2001-2401 | 短期借款、应付账款、应付职工薪酬、应交税费 |
| 所有者权益 | 3001-3101 | 实收资本、资本公积、盈余公积、未分配利润 |
| 成本 | 4001-4401 | 生产成本、制造费用 |
| 损益-收入 | 5001-5301 | 主营业务收入、其他业务收入 |
| 损益-费用 | 5401-5801 | 主营业务成本、销售费用、管理费用、财务费用 |

---

## 3. REST API 设计

### 3.1 通用约定

- 基础路径：`/api/v1/`
- 响应格式：`{ "code": 200, "data": {...}, "message": "ok" }`
- 分页参数：`?page=1&page_size=20`
- 错误响应：`{ "code": 400/500, "data": null, "message": "错误描述" }`

### 3.2 银行对账 API

| 方法 | 路径 | 说明 | 请求/响应要点 |
|------|------|------|---------------|
| GET | `/reconciliation/transactions` | 获取银行流水列表 | query: period, status, min_amount, max_amount; 分页 |
| GET | `/reconciliation/book-entries` | 获取账簿记录列表 | query: period, account_code; 分页 |
| GET | `/reconciliation/status` | 获取对账统计概览 | response: match_rate, unmatched_count, unmatched_amount |
| POST | `/reconciliation/match` | 执行自动匹配 | body: { period }; response: { matched, unmatched, details[] } |
| POST | `/reconciliation/manual-match` | 手动匹配 | body: { bank_ids[], book_ids[] } |
| POST | `/reconciliation/exclude` | 排除项 | body: { transaction_id, reason } |
| GET | `/reconciliation/unmatched` | 获取未匹配项 | query: period; 分类返回 |

### 3.3 税务数据 API

| 方法 | 路径 | 说明 | 请求/响应要点 |
|------|------|------|---------------|
| GET | `/tax/mappings` | 获取科目-税目映射 | query: form_type |
| PUT | `/tax/mappings/:id` | 更新映射关系 | body: { tax_line_no, data_source } |
| GET | `/tax/filing/:form_type` | 获取申报表数据 | query: period; response: 行项数组 |
| POST | `/tax/filing/generate` | 生成申报表 | body: { form_type, period } |
| PUT | `/tax/filing/adjust` | 手动调整申报行项 | body: { line_id, adjusted_value, reason } |
| GET | `/tax/estimate` | 获取税额预估 | query: period; response: 各税种预估 |
| GET | `/tax/validation/:form_type` | 获取校验结果 | query: period; response: 校验项数组 |

### 3.4 财务报表 API

| 方法 | 路径 | 说明 | 请求/响应要点 |
|------|------|------|---------------|
| GET | `/reports/:type` | 获取报表数据 | type: balance_sheet/income/cash_flow; query: period |
| POST | `/reports/generate` | 一键生成报表 | body: { period }; 生成三大报表 |
| GET | `/reports/drill-down` | 钻取明细 | query: report_type, line_no, period, level |
| GET | `/reports/indicators` | 获取财务指标 | query: period; response: 指标数组 |
| GET | `/reports/trend` | 获取趋势数据 | query: report_type, line_no, periods[] |

### 3.5 成本分摊 API

| 方法 | 路径 | 说明 | 请求/响应要点 |
|------|------|------|---------------|
| GET | `/cost-alloc/centers` | 获取成本中心树 | response: 树形结构 |
| GET | `/cost-alloc/pools` | 获取费用池列表 | query: period |
| GET | `/cost-alloc/rules` | 获取分摊规则列表 | - |
| POST | `/cost-alloc/rules` | 创建分摊规则 | body: { name, cost_pool_id, allocation_basis, ... } |
| PUT | `/cost-alloc/rules/:id` | 更新分摊规则 | body: 同上 |
| POST | `/cost-alloc/calculate` | 执行分摊计算 | body: { period }; response: 分摊结果 |
| POST | `/cost-alloc/simulate` | 模拟分摊（不保存） | body: { period, rules[] }; response: 模拟结果 |
| GET | `/cost-alloc/results` | 获取分摊结果 | query: period; response: 结果+桑基图数据 |
| GET | `/cost-alloc/voucher` | 获取分摊凭证 | query: period |

### 3.6 AI 对话 API

| 方法 | 路径 | 说明 | 请求/响应要点 |
|------|------|------|---------------|
| POST | `/ai/chat` | AI 对话（SSE 流式） | body: { message, module_context, history[] }; response: SSE stream |

AI 对话采用 **SSE (Server-Sent Events)** 流式返回，提升交互体验。Agent Router 基于 `module_context`（当前页面模块）自动限定工具集范围，无需跨模块路由。

### 3.7 通用 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查（含数据库状态） |
| GET | `/dashboard/summary` | Dashboard 汇总数据 |

---

## 4. 功能模块详细设计

### 4.1 银行对账自动化

#### 数据模型

```python
class BankTransaction(Base):
    id: int                    # 主键
    account_no: str            # 银行账号
    transaction_date: date     # 交易日期
    amount: Decimal            # 金额（正为收入，负为支出）
    counterparty: str          # 对方户名
    summary: str               # 摘要
    serial_no: str             # 流水号
    currency: str              # 币种（默认 CNY）
    matched_status: str        # 匹配状态: unmatched/matched/confirmed/excluded

class BookEntry(Base):
    id: int
    entry_date: date           # 记账日期
    amount: Decimal            # 金额
    account_code: str          # 科目编码
    account_name: str          # 科目名称
    voucher_no: str            # 凭证号
    summary: str               # 摘要
    auxiliary: str             # 辅助核算（客户/供应商）

class ReconciliationRecord(Base):
    id: int
    match_group_id: str        # 匹配组ID（支持一对多/多对一归组）
    bank_transaction_id: int   # 银行流水 ID
    book_entry_id: int         # 账簿记录 ID
    match_type: str            # 匹配类型: exact/fuzzy/smart/manual
    confidence_score: float    # 匹配置信度 0-1
    is_confirmed: bool         # 是否已人工确认
    match_rule: str            # 匹配规则描述

class ReconciliationRule(Base):
    id: int
    name: str                  # 规则名称
    match_fields: JSON         # 匹配字段组合
    tolerance_days: int        # 日期容差天数
    tolerance_amount: Decimal  # 金额容差
    priority: int              # 优先级
```

#### 功能流程

1. **数据导入**
   - 上传 Excel/CSV 银行对账单
   - 解析并标准化格式（统一日期、金额正负号）
   - Mock：预置 2024年1-3月 约200条真实感银行流水

2. **三级匹配引擎**
   - **L1 精确匹配**：金额完全一致 + 日期相同 → 置信度 1.0
   - **L2 模糊匹配**：金额一致 + 日期容差3天 + 摘要相似度 > 0.7 → 置信度 0.7-0.9
   - **L3 智能匹配**：一对多/多对一拆分匹配（如一笔银行入账对应多张发票合计）→ 置信度 0.5-0.7
   - 匹配结果按置信度排序展示

3. **差异处理**
   - 未匹配项分类：单边银行项、单边账簿项、金额差异项
   - 支持手动匹配、排除、标记待查
   - 差异统计仪表盘

4. **AI Agent 分析**
   - 调用 Claude 分析未匹配原因（重复入账、跨期、手续费未记账、退款冲抵等）
   - 生成对账差异报告（Markdown 格式）
   - 对话式查询："最近一个月有哪些大额未匹配项？"

#### UI 设计

- **主视图**：左右双栏（银行流水 | 账簿记录），中间匹配连线
- **顶部仪表盘**：总匹配率（环形图）、未匹配金额、本期差异趋势
- **状态色标**：绿色已匹配 / 黄色待确认 / 红色异常
- **右侧面板**：AI 助手，可对话查询对账情况

---

### 4.2 税务数据准备

> **范围限定**：税务申报覆盖增值税（主表 + 附表一 + 附表二）和企业所得税季度预缴表。年度汇算清缴不在本期范围内。`TaxFilingTemplate.form_type` 取值限定为 `vat_general`（增值税一般纳税人）和 `cit_quarterly`（企业所得税季度预缴）。

#### 数据模型

```python
class TaxMapping(Base):
    id: int
    account_code: str          # 会计科目编码
    account_name: str          # 会计科目名称
    tax_form_type: str         # 申报表类型（增值税/企业所得税）
    tax_line_no: str           # 申报表行号
    tax_line_name: str         # 申报表行项名称
    data_source: str           # 取数方式（本期发生额/期末余额/累计发生额）

class TaxFilingTemplate(Base):
    id: int
    form_type: str             # 申报表类型
    form_name: str             # 申报表名称（增值税主表/附表一/附表二...）
    period_type: str           # 申报周期（月度/季度/年度）

class TaxLineItem(Base):
    id: int
    template_id: int           # 模板 ID
    line_no: str               # 行号
    line_name: str             # 行项名称
    formula: str               # 计算公式（引用其他行或科目数据）
    current_value: Decimal     # 当期值
    adjusted_value: Decimal    # 调整后值（手动修正）
    period: str                # 所属期间

class TaxEstimate(Base):
    id: int
    tax_type: str              # 税种
    period: str                # 期间
    taxable_amount: Decimal    # 应纳税所得额/销售额
    tax_amount: Decimal        # 应纳税额
    previous_period: Decimal   # 上期税额（用于对比）
    yoy_change: float          # 同比变化率

class TaxValidationRule(Base):
    id: int
    form_type: str             # 申报表类型
    rule_name: str             # 规则名称
    rule_expression: str       # 校验表达式（如 "line_1 == line_2 + line_3"）
    severity: str              # 严重度：error/warning
```

#### 功能流程

1. **科目映射配置**
   - 可视化界面配置会计科目 → 申报表行项映射
   - 预置标准映射模板（小企业会计准则）
   - 支持自定义调整

2. **数据自动提取**
   - 从科目余额表按映射规则自动汇总
   - 支持多种取数方式：本期发生额、期末余额、累计数
   - 数据来源可追溯（点击金额 → 查看明细科目和凭证）

3. **申报表生成**
   - 增值税申报表（主表 + 附表一至四）
   - 企业所得税季度预缴表
   - 表格格式仿真实国税申报表样式
   - 支持手动调整并记录调整原因

4. **智能校验**
   - 表内勾稽：如 销项税额 = 不含税销售额 × 税率
   - 表间关联：附表数据与主表一致性
   - 合理性预警：税负率与行业平均对比
   - 校验结果以红/黄标记展示

5. **AI Agent 分析**
   - 识别税务风险点（进项不足、税负率偏离行业均值）
   - 政策影响提示（如小微企业优惠政策适用性）
   - 自然语言查询："本季度增值税税负率是多少？和去年同期比怎么样？"

#### UI 设计

- **申报表预览**：仿国税申报表格式，自动填充 + 可编辑
- **取数溯源**：点击数字 → 弹出科目明细和凭证来源
- **税额仪表盘**：各税种预估金额、同比环比柱状图、税负率趋势
- **校验面板**：校验结果列表，红色错误 / 黄色预警

---

### 4.3 财务报表生成

#### 数据模型

```python
class AccountBalance(Base):
    id: int
    account_code: str          # 科目编码
    account_name: str          # 科目名称
    account_level: int         # 科目级别（1-4级）
    parent_code: str           # 上级科目编码
    period: str                # 期间（如 2024-03）
    opening_balance: Decimal   # 期初余额
    debit_amount: Decimal      # 本期借方发生额
    credit_amount: Decimal     # 本期贷方发生额
    closing_balance: Decimal   # 期末余额
    balance_direction: str     # 余额方向（debit/credit，UI层本地化为借/贷）

class ReportTemplate(Base):
    id: int
    report_type: str           # 报表类型：balance_sheet/income/cash_flow
    line_no: str               # 行号
    line_name: str             # 项目名称
    formula: str               # 取数公式（引用科目或其他行）
    indent_level: int          # 缩进级别（用于展示层级）
    is_total: bool             # 是否合计行
    display_order: int         # 显示顺序

class ReportData(Base):
    id: int
    report_type: str           # 报表类型
    period: str                # 期间
    line_no: str               # 行号
    current_amount: Decimal    # 本期金额
    previous_amount: Decimal   # 上期金额
    yoy_change: float          # 同比变化率

class FinancialIndicator(Base):
    id: int
    period: str                # 期间
    indicator_name: str        # 指标名称
    indicator_value: float     # 指标值
    benchmark_value: float     # 行业基准值
    health_status: str         # 健康度：good/warning/danger
    description: str           # AI 生成的解读文字
```

#### 功能流程

1. **一键生成三大报表**
   - 资产负债表：按流动性排列，自动平衡校验（资产 = 负债 + 所有者权益）
   - 利润表：收入 → 成本 → 毛利 → 费用 → 营业利润 → 净利润 层级展示
   - 现金流量表：间接法编制，从净利润逐项调整到经营活动现金流
   - 数据从科目余额表自动取数

2. **三级钻取**
   - L1 报表项（如"应收账款"） → L2 明细科目（一级、二级科目） → L3 凭证明细
   - 钻取时动画过渡，面包屑导航支持快速返回
   - 钻取后展示明细表格

3. **多期对比分析**
   - 支持月度/季度/年度切换
   - 同比/环比自动计算
   - ECharts 趋势折线图 + 结构饼图（资产构成、费用构成等）

4. **AI 财务分析**
   - 自动计算关键财务指标：
     - 偿债能力：流动比率、速动比率、资产负债率
     - 盈利能力：毛利率、净利率、ROE、ROA
     - 运营能力：应收账款周转率、存货周转率
   - 指标健康度评估（对比行业基准）
   - 自然语言解读："本季度流动比率为 1.8，高于行业均值 1.5，短期偿债能力良好..."
   - 对话式查询："哪些费用科目增长最快？"

#### UI 设计

- **报表 Tab 切换**：资产负债表 | 利润表 | 现金流量表
- **左侧报表主体**：标准财务报表格式，支持点击钻取
- **右侧 AI 面板**：财务指标卡片（带健康度色标）+ AI 解读文字
- **底部图表区**：ECharts 趋势图、结构图，支持切换时间维度
- **钻取交互**：点击金额 → 面包屑导航 → 明细展开动画

---

### 4.4 成本分摊计算

#### 数据模型

```python
class CostCenter(Base):
    id: int
    code: str                  # 成本中心编码
    name: str                  # 名称
    center_type: str           # 类型：department/project/product_line
    parent_id: int             # 上级成本中心
    headcount: int             # 人数
    area: float                # 办公面积（平方米）
    revenue_ratio: float       # 收入占比

class CostPool(Base):
    id: int
    name: str                  # 费用池名称
    cost_type: str             # 费用类型：rent/utilities/it/management/other
    account_code: str          # 归集科目编码
    period: str                # 期间
    amount: Decimal            # 当期金额
    is_allocated: bool         # 是否已分摊

class AllocationRule(Base):
    id: int
    name: str                  # 规则名称
    cost_pool_id: int          # 费用池 ID
    allocation_basis: str      # 分摊基础：headcount/area/revenue/hours/custom
    condition_expr: str        # 条件表达式（IF-THEN 逻辑）
    priority: int              # 优先级
    effective_from: date       # 生效起始日
    effective_to: date         # 生效结束日

class AllocationResult(Base):
    id: int
    rule_id: int               # 规则 ID
    cost_pool_id: int          # 源费用池 ID
    cost_center_id: int        # 目标成本中心 ID
    period: str                # 期间
    allocated_amount: Decimal  # 分摊金额
    allocation_ratio: float    # 分摊比例
    calculation_detail: str    # 计算明细（JSON）

class AllocationVoucher(Base):
    id: int
    period: str                # 期间
    voucher_no: str            # 凭证号
    entries: JSON              # 分录明细[{debit_account, credit_account, amount, cost_center}]
    status: str                # 状态：draft/confirmed
```

#### 功能流程

1. **成本中心管理**
   - 树形结构管理（公司 → 事业部 → 部门）
   - 配置权重属性：人数、面积、收入占比
   - Mock 预置：5个部门，各有人数和面积数据

2. **费用池归集**
   - 从账簿按科目自动归集待分摊费用
   - 预置费用池：办公租金、水电费、IT运维费、管理层薪资、折旧摊销
   - 显示各池当期金额和历史趋势

3. **规则引擎配置**
   - 可视化 IF-THEN 规则编辑器
   - 预置规则示例：
     - "办公租金 → 按面积占比分摊"
     - "IT运维费 → 按人数占比分摊"
     - "管理层薪资 → 按收入占比分摊"
   - 规则优先级排序，支持生效期间管理

4. **分摊计算与预览**
   - 一键执行分摊计算
   - 桑基图展示费用流向（费用池 → 成本中心）
   - 分摊结果表格：各成本中心承担的各项费用明细
   - 对比模拟：调整规则参数后实时预览变化
   - 自动生成分摊会计分录（凭证预览）

5. **AI Agent 优化**
   - 分析历史分摊趋势（某部门费用占比是否异常增长）
   - 合理性检查（分摊后单人费用是否偏离均值）
   - 建议优化方案（"建议将IT费用从按人数改为按设备数分摊，更精准反映实际使用"）
   - 对话查询："研发部门本季度的分摊费用构成是什么？"

#### UI 设计

- **左侧**：成本中心树形结构（可展开/折叠）
- **中央**：
  - 费用池卡片（显示金额和状态）
  - 规则配置面板（IF-THEN 可视化编辑器）
  - 分摊结果表格
- **右侧**：桑基图展示分摊流向
- **底部**：分摊前后对比、凭证预览
- **AI 面板**：分摊合理性分析 + 优化建议

---

## 5. AI Agent 统一架构

### 5.1 Agent 设计

基于 Claude API tool_use 实现多步推理 Agent：

```
用户自然语言提问
       ↓
   Agent Router（识别问题所属模块）
       ↓
   组装上下文 + 工具集
       ↓
   Claude API (tool_use 多轮调用)
       ↓
   结构化结果 → 前端渲染
```

### 5.2 Agent 工具集

| 工具 | 功能 | 所属模块 |
|------|------|----------|
| `query_bank_transactions` | 查询银行流水（按日期/金额/对方筛选） | 银行对账 |
| `query_book_entries` | 查询账簿记录 | 银行对账 |
| `get_reconciliation_status` | 获取对账匹配状态和统计 | 银行对账 |
| `analyze_unmatched_items` | 分析未匹配项详情 | 银行对账 |
| `query_tax_data` | 查询税务申报数据 | 税务准备 |
| `calculate_tax_estimate` | 计算预估税额 | 税务准备 |
| `check_tax_compliance` | 校验税务合规性 | 税务准备 |
| `generate_financial_report` | 生成指定报表 | 财务报表 |
| `calculate_financial_indicators` | 计算财务指标 | 财务报表 |
| `drill_down_report_item` | 钻取报表明细 | 财务报表 |
| `query_cost_allocation` | 查询分摊数据 | 成本分摊 |
| `simulate_allocation` | 模拟分摊计算 | 成本分摊 |
| `compare_allocation_schemes` | 对比不同分摊方案 | 成本分摊 |

### 5.3 交互设计

- 每个功能模块页面右下角有 AI 助手浮动按钮
- 点击展开对话面板（抽屉式）
- 支持自然语言查询和分析请求
- 回复以结构化卡片 + 文字说明混合展示
- 关键数据引用支持点击跳转到对应模块

---

## 6. Mock 数据设计

### 6.1 数据规模

为确保演示逼真，预置以下 Mock 数据：

| 数据类型 | 规模 | 时间范围 |
|----------|------|----------|
| 银行流水 | ~200条 | 2024-01 至 2024-03 |
| 账簿凭证 | ~180条 | 2024-01 至 2024-03 |
| 科目余额表 | ~60个科目 × 3个月 | 2024-01 至 2024-03 |
| 成本中心 | 5个部门 | - |
| 公共费用 | 5类费用池 × 3个月 | 2024-01 至 2024-03 |

### 6.2 数据真实感设计

- 使用一家虚拟科技公司 "星辰科技有限公司" 的数据
- 银行流水包含：客户回款、供应商付款、工资发放、社保公积金、税款缴纳、水电费等
- 故意设置约 15% 的未匹配项（跨期、拆分、手续费等场景）
- 财务数据符合基本会计逻辑（借贷平衡、科目勾稽）
- 税务数据符合中国增值税/企业所得税基本逻辑

---

## 7. 首页仪表盘

Dashboard 汇总展示四大模块核心指标：

- **对账状态**：当月匹配率、未匹配金额
- **税务概览**：本期预估税额、税负率
- **财务快照**：总资产、净利润、现金余额（迷你报表）
- **分摊状态**：本月待分摊总额、已分摊进度
- **AI 洞察卡片**：最新异常提醒和建议（如"发现3笔超过30天未匹配的银行流水"）

---

## 8. 验证方案

### 8.1 后端验证

```bash
# 在 venv 中启动后端
cd FinMate && source venv/bin/activate
cd backend && uvicorn app.main:app --reload --port 8000

# 验证 API
curl http://localhost:8000/docs          # Swagger 文档
curl http://localhost:8000/api/reconciliation/status
curl http://localhost:8000/api/tax/estimate
curl http://localhost:8000/api/reports/balance-sheet?period=2024-03
curl http://localhost:8000/api/cost-alloc/results?period=2024-03
```

### 8.2 前端验证

```bash
cd FinMate/frontend && npm run dev
# 访问 http://localhost:5173
```

验证清单：
- [ ] Dashboard 仪表盘数据正确展示
- [ ] 银行对账：左右双栏展示、匹配连线、AI 分析
- [ ] 税务准备：申报表自动填充、校验结果、税额预估
- [ ] 财务报表：三大报表生成、三级钻取、指标分析
- [ ] 成本分摊：规则配置、桑基图、分摊结果
- [ ] AI 助手：各模块对话查询正常响应

### 8.3 端到端演示流程

1. 打开 Dashboard → 查看全局概览
2. 进入银行对账 → 查看自动匹配结果 → AI 分析未匹配项
3. 进入税务准备 → 查看自动生成的申报表 → 校验结果 → AI 风险提示
4. 进入财务报表 → 切换三大报表 → 钻取明细 → AI 指标分析
5. 进入成本分摊 → 查看规则和分摊流向 → 调整规则模拟 → AI 优化建议
