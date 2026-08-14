import { useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { App, Avatar, Button, Layout, Menu, Space, Typography } from 'antd'
import {
  AppstoreOutlined,
  AuditOutlined,
  BuildOutlined,
  FolderOpenOutlined,
  KeyOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import { api, setAccessToken } from '../api'
import { useAuthStore } from '../store'

const { Header, Sider, Content } = Layout

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const user = useAuthStore((state) => state.user)!
  const setUser = useAuthStore((state) => state.setUser)
  const navigate = useNavigate()
  const location = useLocation()
  const { message } = App.useApp()
  const items = [
    { key: '/', icon: <AppstoreOutlined />, label: '仪表盘' },
    { key: '/projects', icon: <FolderOpenOutlined />, label: '项目' },
    { key: '/builds', icon: <BuildOutlined />, label: '构建任务' },
    ...(user.role === 'admin'
      ? [
          { key: '/credentials', icon: <KeyOutlined />, label: '仓库凭据' },
          { key: '/users', icon: <TeamOutlined />, label: '用户' },
          { key: '/audit', icon: <AuditOutlined />, label: '审计日志' },
        ]
      : []),
  ]
  const selected =
    items.find((item) => item.key !== '/' && location.pathname.startsWith(item.key))?.key || '/'
  const logout = async () => {
    try {
      await api.post('/auth/logout')
    } catch {
      /* cookie may already be invalid */
    }
    setAccessToken('')
    setUser(null)
    message.success('已退出登录')
  }
  return (
    <Layout className="app-shell">
      <Sider trigger={null} collapsible collapsed={collapsed} width={232} className="app-sider">
        <div className="brand">
          <span className="brand-mark">U</span>
          {!collapsed && <span>WGT Builder</span>}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selected]}
          items={items}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header className="app-header">
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />
          <Space size="middle">
            <Avatar>{user.username.slice(0, 1).toUpperCase()}</Avatar>
            <div className="user-meta">
              <Typography.Text strong>{user.username}</Typography.Text>
              <small>{user.role}</small>
            </div>
            <Button type="text" icon={<LogoutOutlined />} onClick={logout}>
              退出
            </Button>
          </Space>
        </Header>
        <Content className="app-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
