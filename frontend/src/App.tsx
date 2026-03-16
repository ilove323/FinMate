import { lazy, Suspense } from 'react'
import { ConfigProvider, Layout, Menu, Spin, theme } from 'antd'
import {
  DashboardOutlined,
  BankOutlined,
  AuditOutlined,
  BarChartOutlined,
  ApartmentOutlined,
} from '@ant-design/icons'
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import AIAssistant from './components/AIAssistant'
import PeriodSelector from './components/PeriodSelector'
import { useChatStore } from './store'
import type { ModuleContext } from './types'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Reconciliation = lazy(() => import('./pages/Reconciliation'))
const Tax = lazy(() => import('./pages/Tax'))
const Reports = lazy(() => import('./pages/Reports'))
const CostAlloc = lazy(() => import('./pages/CostAlloc'))

const { Sider, Content } = Layout

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '仪表盘', ctx: null },
  { key: '/reconciliation', icon: <BankOutlined />, label: '银行对账', ctx: 'reconciliation' },
  { key: '/tax', icon: <AuditOutlined />, label: '税务准备', ctx: 'tax' },
  { key: '/reports', icon: <BarChartOutlined />, label: '财务报表', ctx: 'reports' },
  { key: '/cost-alloc', icon: <ApartmentOutlined />, label: '成本分摊', ctx: 'cost_alloc' },
]

function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const setModuleContext = useChatStore((s) => s.setModuleContext)

  const handleMenuClick = ({ key }: { key: string }) => {
    const item = menuItems.find((m) => m.key === key)
    setModuleContext((item?.ctx ?? null) as ModuleContext)
    navigate(key)
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* Left nav */}
      <Sider theme="light" width={200}>
        <div style={{
          height: 64, display: 'flex', alignItems: 'center',
          justifyContent: 'center', fontWeight: 'bold', fontSize: 18,
          borderBottom: '1px solid #f0f0f0',
        }}>
          FinMate
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>

      <Layout>
        {/* Top bar */}
        <div style={{
          height: 56, background: '#fff', padding: '0 24px',
          display: 'flex', alignItems: 'center', gap: 12,
          borderBottom: '1px solid #f0f0f0', flexShrink: 0,
        }}>
          <span style={{ fontWeight: 600, fontSize: 16 }}>AI 财务助理</span>
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 13, color: '#666' }}>期间：</span>
            <PeriodSelector />
          </div>
        </div>

        <Layout style={{ overflow: 'hidden' }}>
          {/* Page content */}
          <Content style={{ padding: 24, overflowY: 'auto' }}>
            <Suspense fallback={<Spin size="large" style={{ display: 'block', margin: '80px auto' }} />}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/reconciliation" element={<Reconciliation />} />
                <Route path="/tax" element={<Tax />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/cost-alloc" element={<CostAlloc />} />
              </Routes>
            </Suspense>
          </Content>

          {/* Right AI chat panel */}
          <Sider
            theme="light"
            width={360}
            style={{ borderLeft: '1px solid #f0f0f0', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}
          >
            <AIAssistant />
          </Sider>
        </Layout>
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
