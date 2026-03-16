import { useEffect, useState } from 'react';
import {
  Alert, Button, Card, Col, Row, Select, Spin, Statistic, Table, Tag, Typography,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { getReport, getFinancialIndicators, generateReports } from '../services/api';
import { usePeriodStore } from '../store';
import AmountCell from '../components/AmountCell';
import type { ReportLine, FinancialIndicator } from '../types';

const { Title } = Typography;

const REPORT_TYPES = [
  { value: 'balance_sheet', label: '资产负债表' },
  { value: 'income', label: '利润表' },
  { value: 'cash_flow', label: '现金流量表' },
];

const healthColor: Record<string, string> = {
  good: 'green', warning: 'orange', danger: 'red',
};
const healthLabel: Record<string, string> = {
  good: '良好', warning: '注意', danger: '风险',
};
const healthValueColor: Record<string, string> = {
  good: '#3f8600', warning: '#d46b08', danger: '#cf1322',
};

export default function Reports() {
  const { period } = usePeriodStore();
  const [reportType, setReportType] = useState('balance_sheet');
  const [lines, setLines] = useState<ReportLine[]>([]);
  const [indicators, setIndicators] = useState<FinancialIndicator[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [report, inds] = await Promise.all([
        getReport(reportType, period),
        getFinancialIndicators(period),
      ]);
      setLines(report.lines ?? []);
      setIndicators(inds);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [period, reportType]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await generateReports(period);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setGenerating(false);
    }
  };

  const columns: ColumnsType<ReportLine> = [
    {
      title: '项目',
      dataIndex: 'line_name',
      render: (v: string, row) => (
        <span style={{ paddingLeft: (row.indent_level ?? 0) * 16, fontWeight: row.is_total ? 600 : 400 }}>
          {v}
        </span>
      ),
    },
    { title: '行次', dataIndex: 'line_no', width: 60, align: 'center' },
    {
      title: '本期金额',
      dataIndex: 'current_amount',
      align: 'right',
      width: 140,
      render: (v: number, row) => (
        <span style={{ fontWeight: row.is_total ? 600 : 400 }}>
          <AmountCell value={v ?? 0} />
        </span>
      ),
    },
    {
      title: '上期金额',
      dataIndex: 'previous_amount',
      align: 'right',
      width: 140,
      render: (v: number | null) => v != null ? <AmountCell value={v} /> : '-',
    },
    {
      title: '同比变动',
      dataIndex: 'yoy_change',
      align: 'right',
      width: 100,
      render: (v: number | null) => v != null ? (
        <Tag color={v > 0 ? 'green' : v < 0 ? 'red' : 'default'}>{v > 0 ? '+' : ''}{v.toFixed(1)}%</Tag>
      ) : '-',
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16, gap: 12 }}>
        <Title level={4} style={{ margin: 0 }}>财务报表 · {period}</Title>
        <Select
          value={reportType}
          onChange={setReportType}
          options={REPORT_TYPES}
          style={{ width: 180 }}
        />
        <Button type="primary" loading={generating} onClick={handleGenerate} style={{ marginLeft: 'auto' }}>
          生成报表
        </Button>
      </div>

      {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} />}

      {/* Financial indicators */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        {indicators.map((ind) => (
          <Col span={6} key={ind.indicator_name}>
            <Card bordered={false} size="small">
              <Statistic
                title={ind.indicator_name}
                value={ind.indicator_value}
                precision={2}
                valueStyle={{ color: healthValueColor[ind.health_status] ?? '#000', fontSize: 20 }}
              />
              <div style={{ marginTop: 4, fontSize: 12, color: '#888' }}>{ind.description}</div>
              <Tag color={healthColor[ind.health_status]} style={{ marginTop: 4 }}>
                {healthLabel[ind.health_status]}
              </Tag>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Report table */}
      <Card title={REPORT_TYPES.find((t) => t.value === reportType)?.label} bordered={false}>
        {loading ? (
          <Spin />
        ) : (
          <Table
            dataSource={lines}
            columns={columns}
            rowKey={(r) => r.line_no}
            size="small"
            pagination={false}
            scroll={{ y: 520 }}
            rowClassName={(row) => row.is_total ? 'report-total-row' : ''}
          />
        )}
      </Card>
    </div>
  );
}
