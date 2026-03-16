import { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic, Progress, Spin, Alert, Typography } from 'antd';
import {
  BankOutlined, AuditOutlined, BarChartOutlined, ApartmentOutlined,
} from '@ant-design/icons';
import { getDashboardSummary } from '../services/api';
import type { DashboardSummary } from '../types';

const { Title } = Typography;

export default function Dashboard() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDashboardSummary()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '80px auto' }} />;
  if (error) return <Alert type="error" message={error} />;
  if (!data) return null;

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>
        总览仪表盘 · {data.period}
      </Title>

      <Row gutter={[16, 16]}>
        {/* Reconciliation */}
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false} style={{ borderRadius: 8 }}>
            <Statistic
              title={<><BankOutlined /> 对账匹配率</>}
              value={data.reconciliation.match_rate}
              suffix="%"
              precision={1}
              valueStyle={{ color: data.reconciliation.match_rate >= 90 ? '#3f8600' : '#cf1322' }}
            />
            <div style={{ marginTop: 8, color: '#888', fontSize: 12 }}>
              未匹配 {data.reconciliation.unmatched_count} 笔
            </div>
            <Progress
              percent={data.reconciliation.match_rate}
              showInfo={false}
              strokeColor={data.reconciliation.match_rate >= 90 ? '#52c41a' : '#ff4d4f'}
              style={{ marginTop: 4 }}
            />
          </Card>
        </Col>

        {/* Tax */}
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false} style={{ borderRadius: 8 }}>
            <Statistic
              title={<><AuditOutlined /> 预估增值税</>}
              value={data.tax.estimated_vat}
              suffix="元"
              precision={2}
            />
            <div style={{ marginTop: 8, color: '#888', fontSize: 12 }}>
              税负率 {data.tax.tax_burden_rate}%
            </div>
          </Card>
        </Col>

        {/* Financial */}
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false} style={{ borderRadius: 8 }}>
            <Statistic
              title={<><BarChartOutlined /> 净利润</>}
              value={data.financial.net_profit}
              suffix="元"
              precision={2}
              valueStyle={{ color: data.financial.net_profit >= 0 ? '#3f8600' : '#cf1322' }}
            />
            <div style={{ marginTop: 8, color: '#888', fontSize: 12 }}>
              总资产 {(data.financial.total_assets / 10000).toFixed(1)} 万元
            </div>
          </Card>
        </Col>

        {/* Cost Allocation */}
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false} style={{ borderRadius: 8 }}>
            <Statistic
              title={<><ApartmentOutlined /> 成本分摊进度</>}
              value={data.cost_allocation.progress}
              suffix="%"
              precision={1}
            />
            <div style={{ marginTop: 8, color: '#888', fontSize: 12 }}>
              待分摊 {(data.cost_allocation.total_pending / 10000).toFixed(1)} 万元
            </div>
            <Progress
              percent={data.cost_allocation.progress}
              showInfo={false}
              style={{ marginTop: 4 }}
            />
          </Card>
        </Col>
      </Row>

      {/* Cash balance card */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} sm={12}>
          <Card title="货币资金余额" bordered={false} style={{ borderRadius: 8 }}>
            <Statistic
              value={data.financial.cash_balance}
              suffix="元"
              precision={2}
              valueStyle={{ fontSize: 28 }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
