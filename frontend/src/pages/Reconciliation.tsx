import { useEffect, useState } from 'react';
import {
  Alert, Button, Card, Col, Row, Spin, Statistic, Table, Tag, Typography,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  getBankTransactions, getReconciliationStatus, runAutoMatch,
} from '../services/api';
import { usePeriodStore } from '../store';
import AmountCell from '../components/AmountCell';
import type { BankTransaction, ReconciliationStatus } from '../types';

const { Title } = Typography;

const statusColor: Record<string, string> = {
  unmatched: 'red', matched: 'blue', confirmed: 'green', excluded: 'default',
};
const statusLabel: Record<string, string> = {
  unmatched: '未匹配', matched: '已匹配', confirmed: '已确认', excluded: '已排除',
};

const columns: ColumnsType<BankTransaction> = [
  { title: '日期', dataIndex: 'transaction_date', width: 110 },
  {
    title: '方向', dataIndex: 'direction', width: 70,
    render: (v: string) => <Tag color={v === 'credit' ? 'green' : 'red'}>{v === 'credit' ? '收' : '付'}</Tag>,
  },
  {
    title: '金额', dataIndex: 'amount', align: 'right', width: 120,
    render: (v: number) => <AmountCell value={v} />,
  },
  { title: '对方户名', dataIndex: 'counterparty', ellipsis: true },
  { title: '摘要', dataIndex: 'summary', ellipsis: true },
  {
    title: '状态', dataIndex: 'matched_status', width: 90,
    render: (v: string) => <Tag color={statusColor[v]}>{statusLabel[v]}</Tag>,
  },
];

export default function Reconciliation() {
  const { period } = usePeriodStore();
  const [status, setStatus] = useState<ReconciliationStatus | null>(null);
  const [txns, setTxns] = useState<BankTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [matching, setMatching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, t] = await Promise.all([
        getReconciliationStatus(period),
        getBankTransactions({ period }),
      ]);
      setStatus(s);
      setTxns(t);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [period]);

  const handleAutoMatch = async () => {
    setMatching(true);
    try {
      await runAutoMatch(period);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setMatching(false);
    }
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '80px auto' }} />;
  if (error) return <Alert type="error" message={error} />;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>银行对账 · {period}</Title>
        <Button
          type="primary"
          loading={matching}
          onClick={handleAutoMatch}
          style={{ marginLeft: 'auto' }}
        >
          自动匹配
        </Button>
      </div>

      {status && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card bordered={false}>
              <Statistic title="匹配率" value={status.match_rate} suffix="%" precision={1}
                valueStyle={{ color: status.match_rate >= 90 ? '#3f8600' : '#cf1322' }} />
            </Card>
          </Col>
          <Col span={6}>
            <Card bordered={false}>
              <Statistic title="总流水" value={status.total_transactions} suffix="笔" />
            </Card>
          </Col>
          <Col span={6}>
            <Card bordered={false}>
              <Statistic title="已匹配" value={status.matched_count} suffix="笔"
                valueStyle={{ color: '#3f8600' }} />
            </Card>
          </Col>
          <Col span={6}>
            <Card bordered={false}>
              <Statistic title="未匹配" value={status.unmatched_count} suffix="笔"
                valueStyle={{ color: status.unmatched_count > 0 ? '#cf1322' : '#3f8600' }} />
            </Card>
          </Col>
        </Row>
      )}

      <Card bordered={false} title="银行流水明细">
        <Table
          dataSource={txns}
          columns={columns}
          rowKey="id"
          size="small"
          pagination={{ pageSize: 20, showSizeChanger: false }}
          scroll={{ x: 700 }}
        />
      </Card>
    </div>
  );
}
