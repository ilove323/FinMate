import { useEffect, useState } from 'react';
import {
  Alert, Button, Card, Col, Row, Spin, Statistic, Table, Typography,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { getAllocationResults, getCostPools, runCalculation } from '../services/api';
import { usePeriodStore } from '../store';
import AmountCell from '../components/AmountCell';
import type { AllocationResult, CostPool } from '../types';

const { Title } = Typography;

const poolColumns: ColumnsType<CostPool> = [
  { title: '费用池', dataIndex: 'name', ellipsis: true },
  { title: '类型', dataIndex: 'cost_type', width: 100 },
  { title: '科目', dataIndex: 'account_code', width: 80 },
  {
    title: '金额', dataIndex: 'amount', align: 'right', width: 120,
    render: (v: number) => <AmountCell value={v} />,
  },
  {
    title: '状态', dataIndex: 'is_allocated', width: 80,
    render: (v: boolean) => <span style={{ color: v ? '#3f8600' : '#cf1322' }}>{v ? '已分摊' : '待分摊'}</span>,
  },
];

const resultColumns: ColumnsType<AllocationResult> = [
  { title: '费用池', dataIndex: 'pool_name', ellipsis: true },
  { title: '成本中心', dataIndex: 'center_name' },
  {
    title: '分摊金额', dataIndex: 'allocated_amount', align: 'right', width: 130,
    render: (v: number) => <AmountCell value={v} />,
  },
  {
    title: '分摊比例', dataIndex: 'allocation_ratio', align: 'right', width: 90,
    render: (v: number) => `${(v * 100).toFixed(2)}%`,
  },
];

export default function CostAlloc() {
  const { period } = usePeriodStore();
  const [pools, setPools] = useState<CostPool[]>([]);
  const [results, setResults] = useState<AllocationResult[]>([]);
  const [totalAllocated, setTotalAllocated] = useState(0);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [p, r] = await Promise.all([
        getCostPools(period),
        getAllocationResults(period),
      ]);
      setPools(p);
      setResults(r.results ?? []);
      setTotalAllocated(r.total_allocated ?? 0);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [period]);

  const handleCalculate = async () => {
    setCalculating(true);
    try {
      const r = await runCalculation(period);
      setResults(r.results ?? []);
      setTotalAllocated(r.total_allocated ?? 0);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setCalculating(false);
    }
  };

  const totalPool = pools.reduce((s, p) => s + p.amount, 0);
  const allocatedPool = pools.filter((p) => p.is_allocated).reduce((s, p) => s + p.amount, 0);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>成本分摊 · {period}</Title>
        <Button
          type="primary"
          loading={calculating}
          onClick={handleCalculate}
          style={{ marginLeft: 'auto' }}
        >
          执行分摊
        </Button>
      </div>

      {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} />}

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Card bordered={false}>
            <Statistic title="费用池总额" value={totalPool} suffix="元" precision={2} />
          </Card>
        </Col>
        <Col span={8}>
          <Card bordered={false}>
            <Statistic title="已分摊金额" value={totalAllocated} suffix="元" precision={2}
              valueStyle={{ color: '#3f8600' }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card bordered={false}>
            <Statistic
              title="分摊进度"
              value={totalPool > 0 ? (allocatedPool / totalPool * 100) : 0}
              suffix="%"
              precision={1}
            />
          </Card>
        </Col>
      </Row>

      {loading ? (
        <Spin size="large" style={{ display: 'block', margin: '40px auto' }} />
      ) : (
        <Row gutter={16}>
          <Col span={12}>
            <Card title="费用池" bordered={false}>
              <Table
                dataSource={pools}
                columns={poolColumns}
                rowKey="id"
                size="small"
                pagination={false}
                scroll={{ y: 400 }}
              />
            </Card>
          </Col>
          <Col span={12}>
            <Card title="分摊结果" bordered={false}>
              <Table
                dataSource={results}
                columns={resultColumns}
                rowKey={(r) => `${r.pool_name}-${r.center_name}`}
                size="small"
                pagination={{ pageSize: 15, showSizeChanger: false }}
                scroll={{ y: 380 }}
              />
            </Card>
          </Col>
        </Row>
      )}
    </div>
  );
}
