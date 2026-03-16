import { Typography } from 'antd';

const { Text } = Typography;

interface Props {
  value: number;
  showSign?: boolean;
}

export default function AmountCell({ value, showSign = false }: Props) {
  const formatted = value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (showSign && value !== 0) {
    return <Text type={value > 0 ? 'success' : 'danger'}>{value > 0 ? '+' : ''}{formatted}</Text>;
  }
  return <span>{formatted}</span>;
}
