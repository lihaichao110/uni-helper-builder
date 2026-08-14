import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  App,
  Button,
  Card,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Table,
  Tag,
  Typography,
} from 'antd'
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons'
import { api } from '../api'
import type { Credential } from '../types'

interface CredentialForm {
  name: string
  type: 'ssh' | 'https-token'
  username?: string
  secret: string
  known_hosts?: string
}

export default function CredentialsPage() {
  const [open, setOpen] = useState(false)
  const [type, setType] = useState<'ssh' | 'https-token'>('ssh')
  const [form] = Form.useForm<CredentialForm>()
  const queryClient = useQueryClient()
  const { message } = App.useApp()
  const { data = [] } = useQuery({
    queryKey: ['credentials'],
    queryFn: () => api.get<Credential[]>('/credentials').then((r) => r.data),
  })
  const create = useMutation({
    mutationFn: (values: CredentialForm) => api.post('/credentials', values),
    onSuccess: () => {
      message.success('凭据已安全保存')
      setOpen(false)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['credentials'] })
    },
    onError: () => message.error('凭据保存失败'),
  })
  const remove = async (id: string) => {
    try {
      await api.delete(`/credentials/${id}`)
      message.success('凭据已删除')
      queryClient.invalidateQueries({ queryKey: ['credentials'] })
    } catch {
      message.error('凭据仍被项目使用或删除失败')
    }
  }
  return (
    <div>
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>仓库凭据</Typography.Title>
          <Typography.Text type="secondary">密钥加密存储且不会在页面回显</Typography.Text>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            form.resetFields()
            setType('ssh')
            setOpen(true)
          }}
        >
          新增凭据
        </Button>
      </div>
      <Card className="content-card">
        <Table
          rowKey="id"
          dataSource={data}
          columns={[
            { title: '名称', dataIndex: 'name' },
            {
              title: '类型',
              dataIndex: 'type',
              render: (value) => <Tag color={value === 'ssh' ? 'purple' : 'blue'}>{value}</Tag>,
            },
            { title: '用户名', dataIndex: 'username', render: (value) => value || '—' },
            {
              title: '主机指纹',
              dataIndex: 'known_hosts',
              ellipsis: true,
              render: (value) => value || '—',
            },
            {
              title: '操作',
              render: (_, item) => (
                <Popconfirm title="确认删除该凭据？" onConfirm={() => remove(item.id)}>
                  <Button type="text" danger icon={<DeleteOutlined />}>
                    删除
                  </Button>
                </Popconfirm>
              ),
            },
          ]}
        />
      </Card>
      <Modal
        title="新增仓库凭据"
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={create.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => create.mutate(values)}
          initialValues={{ type: 'ssh' }}
        >
          <Form.Item name="name" label="凭据名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="type" label="类型" rules={[{ required: true }]}>
            <Select
              onChange={setType}
              options={[
                { value: 'ssh', label: 'SSH 部署密钥' },
                { value: 'https-token', label: 'HTTPS Token' },
              ]}
            />
          </Form.Item>
          {type === 'https-token' && (
            <Form.Item name="username" label="用户名">
              <Input placeholder="未填写时使用 oauth2" />
            </Form.Item>
          )}
          <Form.Item
            name="secret"
            label={type === 'ssh' ? 'SSH 私钥' : '访问 Token'}
            rules={[{ required: true }]}
          >
            <Input.TextArea rows={6} autoComplete="off" />
          </Form.Item>
          {type === 'ssh' && (
            <Form.Item name="known_hosts" label="known_hosts 主机指纹" rules={[{ required: true }]}>
              <Input.TextArea rows={4} placeholder="由 ssh-keyscan 获取并由管理员核对" />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  )
}
