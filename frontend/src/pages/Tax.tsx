import { useEffect, useState } from 'react';
import {
  Alert, Card, Col, Row, Select, Spin, Statistic, Table, Tag, Typography, Button,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { getTaxFiling, getTaxEstimate, getTaxValidation, generateTaxFiling } from '../services/api';
import { usePeriodStore } from '../store';
import AmountCell from '../components/AmountCell';
import type { TaxLineItem, TaxEstimateItem, TaxValidation } from '../types';

const { Title } = Typography;

const FORM_TYPES = [
  { value: 'vat_general', label: '增值税申报表（一般纳税人）' },
  { value: 'cit_quarterly', label: '企业所得税季度申报表' },
];

const lineColumns: ColumnsType<TaxLineItem> = [
  { title: '行次', dataIndex: 'line_no', width: 60 },
  { title: '项目', dataIndex: 'line_name' },
  {
    title: '金额', dataIndex: 'amount', align: 'right', width: 130,
    render: (v: number) => <AmountCell value={v} />,
  },
  {
    title: '税额', dataIndex: 'tax_amount', align: 'right', width: 110,
    render: (v?: number) => v != null ? <AmountCell value={v} /> : '-',
  },
];

export default function Tax() {
  const { period } = usePeriodStore();
  const [formType, setFormType] = useState('vat_general');
  const [items, setItems] = useState<TaxLineItem[]>([]);
  const [estimates, setEstimates] = useState<TaxEstimateItem[]>([]);
  const [validation, setValidation] = useState<TaxValidation | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [filing, est, val] = await Promise.all([
        getTaxFiling(formType, period),
        getTaxEstimate(period),
        getTaxValidation(formType, period),
      ]);
      setItems(filing.items ?? []);
      setEstimates(est);
      setValidation(val);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [period, formType]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await generateTaxFiling(formType, period);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16, gap: 12 }}>
        <Title level={4} style={{ margin: 0 }}>税务准备 · {period}</Title>
        <Select
          value={formType}
          onChange={setFormType}
          options={FORM_TYPES}
          style={{ width: 260 }}
        />
        <Button type="primary" loading={generating} onClick={handleGenerate} style={{ marginLeft: 'auto' }}>
          生成申报表
        </Button>
      </div>

      {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} />}

      {/* Tax estimates */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        {estimates.map((e) => (
          <Col span={8} key={e.tax_type}>
            <Card bordered={false}>
              <Statistic
                title={`预估${e.tax_type}`}
                value={e.tax_amount}
                suffix="元"
                precision={2}
              />
              <div style={{ fontSize: 12, color: '#888', marginTop: 4 }}>
                税率 {(e.tax_rate * 100).toFixed(0)}%，应税额 {e.taxable_amount.toLocaleString('zh-CN', { maximumFractionDigits: 2 })} 元
              </div>
            </Card>
          </Col>
        ))}
        {validation && (
          <Col span={8}>
            <Card bordered={false}>
              <Statistic
                title="合规状态"
                value={validation.is_compliant ? '通过' : `${validation.issues.length} 项问题`}
                valueStyle={{ color: validation.is_compliant ? '#3f8600' : '#cf1322' }}
              />
              {validation.issues.slice(0, 2).map((iss, i) => (
                <div key={i} style={{ fontSize: 12, color: '#cf1322', marginTop: 4 }}>
                  {iss.description}
                </div>
              ))}
            </Card>
          </Col>
        )}
      </Row>

      {/* Filing table */}
      <Card
        title="申报表明细"
        bordered={false}
        extra={validation && (
          <Tag color={validation.is_compliant ? 'green' : 'red'}>
            {validation.is_compliant ? '数据合规' : '存在问题'}
          </Tag>
        )}
      >
        {loading ? (
          <Spin />
        ) : (
          <Table
            dataSource={items}
            columns={lineColumns}
            rowKey={(r) => r.line_no}
            size="small"
            pagination={false}
            scroll={{ y: 480 }}
          />
        )}
      </Card>
    </div>
  );
}
