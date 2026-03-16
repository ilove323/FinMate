import { Select } from 'antd';
import { usePeriodStore } from '../store';

const PERIODS = ['2024-01', '2024-02', '2024-03'];

export default function PeriodSelector() {
  const { period, setPeriod } = usePeriodStore();
  return (
    <Select
      value={period}
      onChange={setPeriod}
      options={PERIODS.map((p) => ({ value: p, label: p }))}
      style={{ width: 120 }}
    />
  );
}
