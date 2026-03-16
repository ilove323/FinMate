import type {
  DashboardSummary,
  ReconciliationStatus,
  BankTransaction,
  BookEntry,
  UnmatchedItems,
  TaxFiling,
  TaxEstimateItem,
  TaxValidation,
  FinancialReport,
  FinancialIndicator,
  DrillDownItem,
  CostCenter,
  CostPool,
  AllocationRule,
  AllocationSummary,
  ModuleContext,
} from '../types';

const BASE = '/api/v1';

async function get<T>(path: string, params?: Record<string, string | number>): Promise<T> {
  const url = new URL(path, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, String(v)));
  }
  const res = await fetch(url.toString());
  const json = await res.json();
  if (json.code !== 200) throw new Error(json.message);
  return json.data as T;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const json = await res.json();
  if (json.code !== 200) throw new Error(json.message);
  return json.data as T;
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

export const getDashboardSummary = () =>
  get<DashboardSummary>(`${BASE}/dashboard/summary`);

// ─── Reconciliation ───────────────────────────────────────────────────────────

export const getReconciliationStatus = (period?: string) =>
  get<ReconciliationStatus>(`${BASE}/reconciliation/status`, period ? { period } : undefined);

export const getBankTransactions = async (params?: {
  period?: string;
  status?: string;
  counterparty?: string;
}): Promise<BankTransaction[]> => {
  const res = await get<{ items: BankTransaction[] }>(`${BASE}/reconciliation/transactions`, params as Record<string, string>);
  return res.items ?? [];
};

export const getBookEntries = async (params?: { period?: string; account_code?: string }): Promise<BookEntry[]> => {
  const res = await get<{ items: BookEntry[] }>(`${BASE}/reconciliation/entries`, params as Record<string, string>);
  return res.items ?? [];
};

export const getUnmatchedItems = (period: string) =>
  get<UnmatchedItems>(`${BASE}/reconciliation/unmatched`, { period });

export const runAutoMatch = (period: string) =>
  post<{ matched: number }>('/reconciliation/auto-match', { period });

export const manualMatch = (txn_id: number, entry_id: number) =>
  post<{ success: boolean }>('/reconciliation/manual-match', { txn_id, entry_id });

// ─── Tax ──────────────────────────────────────────────────────────────────────

export const getTaxFiling = (form_type: string, period: string) =>
  get<TaxFiling>(`${BASE}/tax/filing`, { form_type, period });

export const getTaxEstimate = (period: string) =>
  get<TaxEstimateItem[]>(`${BASE}/tax/estimate`, { period });

export const getTaxValidation = (form_type: string, period: string) =>
  get<TaxValidation>(`${BASE}/tax/validation`, { form_type, period });

export const generateTaxFiling = (form_type: string, period: string) =>
  post<TaxFiling>('/tax/generate', { form_type, period });

// ─── Reports ──────────────────────────────────────────────────────────────────

export const getReport = (report_type: string, period: string) =>
  get<FinancialReport>(`${BASE}/reports/${report_type}`, { period });

export const generateReports = (period: string) =>
  post<{ generated: string[] }>('/reports/generate', { period });

export const getFinancialIndicators = (period: string) =>
  get<FinancialIndicator[]>(`${BASE}/reports/indicators`, { period });

export const drillDown = (
  report_type: string,
  line_no: string,
  period: string,
  level = 1
) => get<{ level: number; items: DrillDownItem[] }>(`${BASE}/reports/drill-down`, {
  report_type, line_no, period, level,
});

export const getReportTrend = (report_type: string, line_no: string, periods: string[]) =>
  get<{ line_no: string; data: Array<{ period: string; amount: number }> }>(
    `${BASE}/reports/trend`,
    { report_type, line_no, periods: periods.join(',') }
  );

// ─── Cost Allocation ──────────────────────────────────────────────────────────

export const getCostCenters = () =>
  get<CostCenter[]>(`${BASE}/cost-alloc/centers`);

export const getCostPools = (period?: string) =>
  get<CostPool[]>(`${BASE}/cost-alloc/pools`, period ? { period } : undefined);

export const getAllocationRules = () =>
  get<AllocationRule[]>(`${BASE}/cost-alloc/rules`);

export const getAllocationResults = (period: string) =>
  get<AllocationSummary>(`${BASE}/cost-alloc/results`, { period });

export const runCalculation = (period: string) =>
  post<AllocationSummary>('/cost-alloc/calculate', { period });

export const simulateAllocation = (period: string) =>
  post<AllocationSummary>('/cost-alloc/simulate', { period });

// ─── AI Chat ──────────────────────────────────────────────────────────────────

export function streamChat(
  message: string,
  moduleContext: ModuleContext,
  history: Array<{ role: string; content: string }>,
  onChunk: (chunk: unknown) => void,
  onDone: () => void,
  onError: (err: Error) => void
): AbortController {
  const controller = new AbortController();

  fetch(`${BASE}/ai-chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, module_context: moduleContext, history }),
    signal: controller.signal,
  })
    .then(async (res) => {
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const raw = line.slice(6);
            if (raw === '[DONE]') { onDone(); return; }
            try { onChunk(JSON.parse(raw)); } catch { /* ignore */ }
          }
        }
      }
      onDone();
    })
    .catch((err) => {
      if (err.name !== 'AbortError') onError(err as Error);
    });

  return controller;
}
