import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  App,
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
} from 'antd'
import { ApiOutlined, EditOutlined, PlusOutlined, StopOutlined } from '@ant-design/icons'
import { api } from '../../api'
import { useAuthStore } from '../../store/auth'
import type { Credential } from '../../types/credential'
import type { Project } from '../../types/project'
import { extractErrorMessage } from '../../utils/error'

type ProjectForm = Omit<Project, 'id' | 'created_at' | 'updated_at'>
const installOptions = ['none', 'npm-ci', 'yarn-frozen', 'pnpm-frozen'].map((value) => ({
  label: value,
  value,
}))

export default function ProjectsPage() {
  const user = useAuthStore((state) => state.user)!
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Project | null>(null)
  const [form] = Form.useForm<ProjectForm>()
  const queryClient = useQueryClient()
  const { message } = App.useApp()
  const { data = [], isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.get<Project[]>('/projects').then((r) => r.data),
  })
  const { data: credentials = [] } = useQuery({
    queryKey: ['credentials'],
    queryFn: () => api.get<Credential[]>('/credentials').then((r) => r.data),
    enabled: user.role === 'admin',
  })
  const save = useMutation({
    mutationFn: (values: ProjectForm) =>
      editing ? api.patch(`/projects/${editing.id}`, values) : api.post('/projects', values),
    onSuccess: () => {
      message.success('项目已保存')
      setOpen(false)
      setEditing(null)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
    onError: (error) => message.error(extractErrorMessage(error, '保存失败，请检查项目配置')),
  })
  const test = async (id: string) => {
    try {
      const { data } = await api.post(`/projects/${id}/test-repository`)
      message.success(`连接成功，发现 ${data.ref_count} 个 Ref`)
    } catch (error) {
      message.error(extractErrorMessage(error, '仓库连接失败，请检查地址和凭据'))
    }
  }
  const disable = async (id: string) => {
    await api.delete(`/projects/${id}`)
    message.success('项目已停用')
    queryClient.invalidateQueries({ queryKey: ['projects'] })
  }
  const showCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({
      default_ref: 'main',
      vue_version: '3',
      install_strategy: 'none',
      node_memory_mb: 2048,
      timeout_minutes: 30,
      is_active: true,
    } as ProjectForm)
    setOpen(true)
  }
  const showEdit = (project: Project) => {
    setEditing(project)
    form.setFieldsValue(project)
    setOpen(true)
  }
  return (
    <div>
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>项目</Typography.Title>
          <Typography.Text type="secondary">配置代码仓库和默认构建参数</Typography.Text>
        </div>
        {user.role === 'admin' && (
          <Button type="primary" icon={<PlusOutlined />} onClick={showCreate}>
            新建项目
          </Button>
        )}
      </div>
      <Card className="content-card">
        <Table
          rowKey="id"
          loading={isLoading}
          dataSource={data}
          columns={[
            {
              title: '名称',
              dataIndex: 'name',
              render: (value, record) => (
                <Space>
                  <Typography.Text strong>{value}</Typography.Text>
                  {!record.is_active && <Tag>已停用</Tag>}
                </Space>
              ),
            },
            { title: '仓库', dataIndex: 'git_url', ellipsis: true },
            { title: '默认 Ref', dataIndex: 'default_ref' },
            {
              title: 'Vue',
              dataIndex: 'vue_version',
              render: (value) => <Tag color="blue">Vue {value}</Tag>,
            },
            { title: '安装策略', dataIndex: 'install_strategy' },
            {
              title: '操作',
              width: 240,
              onCell: () => ({ className: 'table-actions' }),
              render: (_, project) =>
                user.role === 'admin' ? (
                  <Space>
                    <Button type="text" icon={<ApiOutlined />} onClick={() => test(project.id)}>
                      测试
                    </Button>
                    <Button type="text" icon={<EditOutlined />} onClick={() => showEdit(project)}>
                      编辑
                    </Button>
                    {project.is_active && (
                      <Popconfirm title="确认停用该项目？" onConfirm={() => disable(project.id)}>
                        <Button type="text" danger icon={<StopOutlined />}>
                          停用
                        </Button>
                      </Popconfirm>
                    )}
                  </Space>
                ) : (
                  '—'
                ),
            },
          ]}
        />
      </Card>
      <Modal
        title={editing ? '编辑项目' : '新建项目'}
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={save.isPending}
        width={680}
      >
        <Form form={form} layout="vertical" onFinish={(values) => save.mutate(values)}>
          <div className="form-grid">
            <Form.Item name="name" label="项目名称" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item name="default_ref" label="默认分支或 Tag" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
          </div>
          <Form.Item name="git_url" label="Git URL" rules={[{ required: true }]}>
            <Input placeholder="git@github.com:org/repo.git 或 https://..." />
          </Form.Item>
          <div className="form-grid">
            <Form.Item name="vue_version" label="Vue 版本" rules={[{ required: true }]}>
              <Select
                options={[
                  { value: '2', label: 'Vue 2' },
                  { value: '3', label: 'Vue 3' },
                ]}
              />
            </Form.Item>
            <Form.Item name="install_strategy" label="依赖安装策略" rules={[{ required: true }]}>
              <Select options={installOptions} />
            </Form.Item>
            <Form.Item name="node_memory_mb" label="Node 内存（MB）">
              <InputNumber min={512} max={8192} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="timeout_minutes" label="超时（分钟）">
              <InputNumber min={5} max={180} style={{ width: '100%' }} />
            </Form.Item>
          </div>
          <Form.Item name="credential_id" label="仓库凭据">
            <Select
              allowClear
              options={credentials.map((c) => ({ value: c.id, label: `${c.name} (${c.type})` }))}
            />
          </Form.Item>
          <Form.Item name="is_active" label="启用" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
