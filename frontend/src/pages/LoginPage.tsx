import { App, Button, Card, Form, Input, Typography } from 'antd'
import { LockOutlined, UserOutlined } from '@ant-design/icons'
import { api, setAccessToken } from '../api'
import { useAuthStore } from '../store'
import type { User } from '../types'
import { extractErrorMessage } from '../utils'

export default function LoginPage() {
  const setUser = useAuthStore((state) => state.setUser)
  const { message } = App.useApp()
  const submit = async (values: { username: string; password: string }) => {
    try {
      const response = await api.post<{ access_token: string; user: User }>('/auth/login', values)
      setAccessToken(response.data.access_token)
      setUser(response.data.user)
    } catch (error) {
      message.error(extractErrorMessage(error, '登录失败，请检查用户名和密码'))
    }
  }
  return (
    <div className="login-page">
      <div className="login-hero">
        <div className="hero-badge">UNI-APP DELIVERY</div>
        <h1>
          让每一次 WGT 构建
          <br />
          清晰、可靠、可追溯
        </h1>
        <p>集中管理代码仓库、构建日志与热更新产物。</p>
      </div>
      <Card className="login-card" variant="borderless">
        <Typography.Title level={2}>欢迎回来</Typography.Title>
        <Typography.Paragraph type="secondary">登录内部构建平台</Typography.Paragraph>
        <Form layout="vertical" size="large" onFinish={submit} requiredMark={false}>
          <Form.Item name="username" label="用户名" rules={[{ required: true }]}>
            <Input prefix={<UserOutlined />} autoFocus />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true }]}>
            <Input.Password prefix={<LockOutlined />} />
          </Form.Item>
          <Button type="primary" htmlType="submit" block>
            登录
          </Button>
        </Form>
      </Card>
    </div>
  )
}
