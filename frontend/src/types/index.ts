// ─── Common ───────────────────────────────────────────────────────────────────

export interface ApiResponse<T> {
  code: number;
  data: T;
  message: string;
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

export interface DashboardSummary {
  period: string;
  reconciliation: { match_rate: number; unmatched_count: number };
  tax: { estimated_vat: number; tax_burden_rate: number };
  financial: { total_assets: number; cash_balance: number; net_profit: number };
  cost_allocation: { total_pending: number; progress: number };
}

// ─── Reconciliation ───────────────────────────────────────────────────────────

export interface BankTransaction {
  id: number;
  transaction_date: string;
  amount: number;
  direction: 'debit' | 'credit';
  counterparty: string;
  description: string;
  matched_status: 'unmatched' | 'matched' | 'confirmed' | 'excluded';
  matched_entry_id?: number;
}

export interface BookEntry {
  id: number;
  voucher_no: string;
  entry_date: string;
  account_code: string;
  account_name: string;
  debit_amount: number;
  credit_amount: number;
  description: string;
  matched_status: string;
}

export interface ReconciliationStatus {
  period: string;
  total_transactions: number;
  matched_count: number;
  unmatched_count: number;
  match_rate: number;
  total_amount: number;
  matched_amount: number;
}

export interface UnmatchedItems {
  period: string;
  bank_only: BankTransaction[];
  book_only: BookEntry[];
}

// ─── Tax ──────────────────────────────────────────────────────────────────────

export interface TaxLineItem {
  line_no: string;
  line_name: string;
  amount: number;
  tax_amount?: number;
  note?: string;
}

export interface TaxFiling {
  form_type: string;
  period: string;
  items: TaxLineItem[];
}

export interface TaxEstimateItem {
  tax_type: string;
  taxable_amount: number;
  tax_amount: number;
  tax_rate: number;
}

export interface TaxValidation {
  form_type: string;
  period: string;
  issues: Array<{ rule: string; description: string; severity: string }>;
  is_compliant: boolean;
}

// ─── Reports ──────────────────────────────────────────────────────────────────

export interface ReportLine {
  line_no: string;
  line_name: string;
  amount: number;
  prev_amount?: number;
  yoy_change?: number;
  indent_level: number;
  is_total: boolean;
}

export interface FinancialReport {
  report_type: string;
  period: string;
  lines: ReportLine[];
}

export interface FinancialIndicator {
  name: string;
  value: number;
  unit: string;
  benchmark?: number;
  status: 'healthy' | 'warning' | 'danger';
}

export interface DrillDownItem {
  account_code?: string;
  account_name?: string;
  amount?: number;
  voucher_no?: string;
  entry_date?: string;
  description?: string;
}

// ─── Cost Allocation ──────────────────────────────────────────────────────────

export interface CostCenter {
  id: number;
  code: string;
  name: string;
  center_type: string;
  headcount: number;
  area: number;
  revenue_ratio: number;
}

export interface CostPool {
  id: number;
  name: string;
  cost_type: string;
  account_code: string;
  period: string;
  amount: number;
  is_allocated: boolean;
}

export interface AllocationRule {
  id: number;
  name: string;
  allocation_basis: 'headcount' | 'area' | 'revenue' | 'equal';
  condition_expr: string;
  priority: number;
}

export interface AllocationResult {
  pool_name: string;
  center_name: string;
  allocated_amount: number;
  allocation_ratio: number;
}

export interface SankeyData {
  nodes: Array<{ name: string }>;
  links: Array<{ source: string; target: string; value: number }>;
}

export interface AllocationSummary {
  period: string;
  total_allocated: number;
  results: AllocationResult[];
  sankey: SankeyData;
}

// ─── AI Chat ──────────────────────────────────────────────────────────────────

export type ChatRole = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: Date;
  toolCalls?: Array<{ tool: string; input: Record<string, unknown> }>;
}

export type ModuleContext = 'reconciliation' | 'tax' | 'reports' | 'cost_alloc' | null;
