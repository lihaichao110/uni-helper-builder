import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Card, Form, Input, Modal, Select, Space, Table, Tag, Typography } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { api } from '../api'
import type { Role, User } from '../types'
import { extractErrorMessage, formatDate } from '../utils'

export default function UsersPage() {
  const [open, setOpen] = useState(false)
  const [form] = Form.useForm<{ username: string; password: string; role: Role }>()
  const queryClient = useQueryClient()
  const { message } = App.useApp()
  const { data = [] } = useQuery({
    queryKey: ['users'],
    queryFn: () => api.get<User[]>('/users').then((r) => r.data),
  })
  const create = useMutation({
    mutationFn: (values: { username: string; password: string; role: Role }) =>
      api.post('/users', values),
    onSuccess: () => {
      message.success('用户已创建')
      setOpen(false)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
    onError: (error) => message.error(extractErrorMessage(error, '创建失败，用户名可能已存在')),
  })
  const update = async (id: string, values: Partial<Pick<User, 'role' | 'is_active'>>) => {
    try {
      await api.patch(`/users/${id}`, values)
      message.success('用户已更新')
      queryClient.invalidateQueries({ queryKey: ['users'] })
    } catch (error) {
      message.error(extractErrorMessage(error, '用户更新失败'))
    }
  }
  return (
    <div>
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>用户</Typography.Title>
          <Typography.Text type="secondary">管理内部平台访问权限</Typography.Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>
          新增用户
        </Button>
      </div>
      <Card className="content-card">
        <Table
          rowKey="id"
          dataSource={data}
          columns={[
            { title: '用户名', dataIndex: 'username' },
            {
              title: '角色',
              dataIndex: 'role',
              render: (value) => <Tag color={value === 'admin' ? 'purple' : 'blue'}>{value}</Tag>,
            },
            {
              title: '状态',
              dataIndex: 'is_active',
              render: (value) => (
                <Tag color={value ? 'success' : 'default'}>{value ? '启用' : '停用'}</Tag>
              ),
            },
            { title: '最后登录', dataIndex: 'last_login_at', render: formatDate },
            { title: '创建时间', dataIndex: 'created_at', render: formatDate },
            {
              title: '操作',
              render: (_, user) => (
                <Space>
                  <Select
                    size="small"
                    value={user.role}
                    style={{ width: 100 }}
                    onChange={(role: Role) => update(user.id, { role })}
                    options={[
                      { value: 'member', label: '成员' },
                      { value: 'admin', label: '管理员' },
                    ]}
                  />
                  <Button
                    size="small"
                    danger={user.is_active}
                    onClick={() => update(user.id, { is_active: !user.is_active })}
                  >
                    {user.is_active ? '停用' : '启用'}
                  </Button>
                </Space>
              ),
            },
          ]}
        />
      </Card>
      <Modal
        title="新增用户"
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={create.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ role: 'member' }}
          onFinish={(values) => create.mutate(values)}
        >
          <Form.Item name="username" label="用户名" rules={[{ required: true, min: 3 }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label="初始密码" rules={[{ required: true, min: 10 }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="role" label="角色">
            <Select
              options={[
                { value: 'member', label: '普通成员' },
                { value: 'admin', label: '管理员' },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
