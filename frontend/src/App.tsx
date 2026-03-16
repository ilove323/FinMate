import { ConfigProvider, Layout, Menu, theme } from 'antd'
import {
  DashboardOutlined,
  BankOutlined,
  AuditOutlined,
  BarChartOutlined,
  ApartmentOutlined,
} from '@ant-design/icons'
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom'

const { Header, Sider, Content } = Layout

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/reconciliation', icon: <BankOutlined />, label: '银行对账' },
  { key: '/tax', icon: <AuditOutlined />, label: '税务准备' },
  { key: '/reports', icon: <BarChartOutlined />, label: '财务报表' },
  { key: '/cost-alloc', icon: <ApartmentOutlined />, label: '成本分摊' },
]

function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="light" width={200}>
        <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: 18 }}>
          FinMate
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', alignItems: 'center' }}>
          <h2 style={{ margin: 0 }}>AI 财务助理</h2>
        </Header>
        <Content style={{ margin: 24, padding: 24, background: '#fff', borderRadius: 8 }}>
          <Routes>
            <Route path="/" element={<div>Dashboard - 即将实现</div>} />
            <Route path="/reconciliation" element={<div>银行对账 - 即将实现</div>} />
            <Route path="/tax" element={<div>税务准备 - 即将实现</div>} />
            <Route path="/reports" element={<div>财务报表 - 即将实现</div>} />
            <Route path="/cost-alloc" element={<div>成本分摊 - 即将实现</div>} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

export default function App() {
  return (
    <ConfigProvider theme={{ algorithm: theme.defaultAlgorithm }}>
      <BrowserRouter>
        <AppLayout />
      </BrowserRouter>
    </ConfigProvider>
  )
}
