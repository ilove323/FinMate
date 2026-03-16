import { useEffect, useState } from 'react';
import { Alert, Card, Input, Spin, Table, Tabs, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { usePeriodStore } from '../store';
import AmountCell from '../components/AmountCell';

const { Title } = Typography;
const BASE = '/api/v1/ledger';

async function fetchJson(url: string) {
  const res = await fetch(url);
  const j = await res.json();
  if (j.code !== 200) throw new Error(j.message);
  return j.data;
}

// ─── Types ────────────────────────────────────────────────────────────────────

interface Account { code: string; name: string; account_type: string; direction: string; level: number; }
interface Balance { account_code: string; account_name: string; opening_balance: number; debit_amount: number; credit_amount: number; closing_balance: number; direction: string; }
interface Entry { id: number; voucher_no: string; entry_date: string; account_code: string; account_name: string; direction: string; debit_amount: number; credit_amount: number; summary: string; }

// ─── Tab 1: 科目余额表 ─────────────────────────────────────────────────────────

const balanceColumns: ColumnsType<Balance> = [
  { title: '科目编码', dataIndex: 'account_code', width: 100 },
  { title: '科目名称', dataIndex: 'account_name', ellipsis: true },
  { title: '方向', dataIndex: 'direction', width: 60, render: (v: string) => <Tag color={v === 'debit' ? 'blue' : 'green'}>{v === 'debit' ? '借' : '贷'}</Tag> },
  { title: '期初余额', dataIndex: 'opening_balance', align: 'right', width: 120, render: (v: number) => <AmountCell value={v} /> },
  { title: '本期借方', dataIndex: 'debit_amount', align: 'right', width: 120, render: (v: number) => <AmountCell value={v} /> },
  { title: '本期贷方', dataIndex: 'credit_amount', align: 'right', width: 120, render: (v: number) => <AmountCell value={v} /> },
  { title: '期末余额', dataIndex: 'closing_balance', align: 'right', width: 120, render: (v: number) => <AmountCell value={v} /> },
];

function BalanceTab({ period }: { period: string }) {
  const [data, setData] = useState<Balance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    setLoading(true);
    fetchJson(`${BASE}/balances?period=${period}`)
      .then(setData).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [period]);

  const filtered = data.filter(r =>
    r.account_code.includes(search) || r.account_name.includes(search)
  );

  if (loading) return <Spin />;
  if (error) return <Alert type="error" message={error} />;

  return (
    <>
      <Input.Search placeholder="搜索科目编码或名称" value={search} onChange={e => setSearch(e.target.value)} style={{ width: 240, marginBottom: 12 }} />
      <Table dataSource={filtered} columns={balanceColumns} rowKey="account_code" size="small" pagination={{ pageSize: 30, showSizeChanger: false }} scroll={{ x: 700 }} />
    </>
  );
}

// ─── Tab 2: 记账凭证 ───────────────────────────────────────────────────────────

const entryColumns: ColumnsType<Entry> = [
  { title: '凭证号', dataIndex: 'voucher_no', width: 140 },
  { title: '日期', dataIndex: 'entry_date', width: 100 },
  { title: '科目', dataIndex: 'account_code', width: 80 },
  { title: '科目名称', dataIndex: 'account_name', ellipsis: true },
  { title: '摘要', dataIndex: 'summary', ellipsis: true },
  { title: '借方金额', dataIndex: 'debit_amount', align: 'right', width: 120, render: (v: number) => v ? <AmountCell value={v} /> : '' },
  { title: '贷方金额', dataIndex: 'credit_amount', align: 'right', width: 120, render: (v: number) => v ? <AmountCell value={v} /> : '' },
];

function EntriesTab({ period }: { period: string }) {
  const [data, setData] = useState<Entry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [acctFilter, setAcctFilter] = useState('');

  const load = (acct: string) => {
    setLoading(true);
    const url = `${BASE}/entries?period=${period}` + (acct ? `&account_code=${acct}` : '');
    fetchJson(url).then(setData).catch((e) => setError(e.message)).finally(() => setLoading(false));
  };

  useEffect(() => { load(''); }, [period]);

  if (error) return <Alert type="error" message={error} />;

  return (
    <>
      <div style={{ marginBottom: 12, display: 'flex', gap: 8 }}>
        <Input placeholder="按科目编码前缀过滤（如：5001）" style={{ width: 240 }}
          onChange={e => setAcctFilter(e.target.value)}
          onPressEnter={() => load(acctFilter)} />
      </div>
      {loading ? <Spin /> : (
        <Table
          dataSource={data} columns={entryColumns} rowKey="id" size="small"
          pagination={{ pageSize: 50, showSizeChanger: false }}
          scroll={{ x: 800 }}
          rowClassName={(_, i) => i % 2 === 0 ? '' : 'ant-table-row-alt'}
        />
      )}
    </>
  );
}

// ─── Tab 3: 会计科目 ───────────────────────────────────────────────────────────

const accountColumns: ColumnsType<Account> = [
  { title: '编码', dataIndex: 'code', width: 100 },
  { title: '名称', dataIndex: 'name', render: (v, r) => <span style={{ paddingLeft: (r.level - 1) * 16 }}>{v}</span> },
  { title: '类型', dataIndex: 'account_type', width: 80 },
  { title: '余额方向', dataIndex: 'direction', width: 80, render: (v: string) => <Tag color={v === 'debit' ? 'blue' : 'green'}>{v === 'debit' ? '借' : '贷'}</Tag> },
  { title: '级次', dataIndex: 'level', width: 60, align: 'center' },
];

function AccountsTab() {
  const [data, setData] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchJson(`${BASE}/accounts`).then(setData).finally(() => setLoading(false));
  }, []);

  const filtered = data.filter(r => r.code.includes(search) || r.name.includes(search));

  if (loading) return <Spin />;
  return (
    <>
      <Input.Search placeholder="搜索科目" value={search} onChange={e => setSearch(e.target.value)} style={{ width: 220, marginBottom: 12 }} />
      <Table dataSource={filtered} columns={accountColumns} rowKey="code" size="small" pagination={{ pageSize: 30 }} />
    </>
  );
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function Ledger() {
  const { period } = usePeriodStore();

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>账簿数据 · {period}</Title>
      <Card bordered={false}>
        <Tabs
          items={[
            { key: 'balances', label: '科目余额表', children: <BalanceTab key={period} period={period} /> },
            { key: 'entries', label: '记账凭证', children: <EntriesTab key={period} period={period} /> },
            { key: 'accounts', label: '会计科目', children: <AccountsTab /> },
          ]}
        />
      </Card>
    </div>
  );
}
