import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { App, AutoComplete, Button, Card, Form, Modal, Select, Table, Tag, Typography } from 'antd'
import { EyeOutlined, PlusOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { api } from '../../api'
import { buildStatusColor } from '../../constants/build'
import type { Build } from '../../types/build'
import type { InstallStrategy, Project } from '../../types/project'
import { buildsRefetchInterval, projectNameMap } from '../../utils/build'
import { formatDate } from '../../utils/format'
import { extractErrorMessage } from '../../utils/error'

interface BuildForm {
  project_id: string
  ref?: string
  vue_version?: '2' | '3'
  install_strategy?: InstallStrategy
}

export default function BuildsPage() {
  const [open, setOpen] = useState(false)
  const [selectedProject, setSelectedProject] = useState('')
  const [form] = Form.useForm<BuildForm>()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { message } = App.useApp()
  const { data: builds = [], isLoading } = useQuery({
    queryKey: ['builds'],
    queryFn: () => api.get<Build[]>('/builds').then((r) => r.data),
    refetchInterval: buildsRefetchInterval,
  })
  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.get<Project[]>('/projects').then((r) => r.data),
  })
  const { data: refs = [], isFetching: refsLoading } = useQuery({
    queryKey: ['project-refs', selectedProject],
    queryFn: () =>
      api
        .get<Array<{ type: string; name: string; sha: string }>>(
          `/projects/${selectedProject}/refs`,
        )
        .then((r) => r.data),
    enabled: Boolean(selectedProject),
  })
  const create = useMutation({
    mutationFn: (values: BuildForm) =>
      api.post<Build>('/builds', values, { headers: { 'Idempotency-Key': crypto.randomUUID() } }),
    onSuccess: (response) => {
      message.success('构建任务已进入队列')
      setOpen(false)
      queryClient.invalidateQueries({ queryKey: ['builds'] })
      navigate(`/builds/${response.data.id}`)
    },
    onError: (error) =>
      message.error(extractErrorMessage(error, '创建失败，该项目可能已有运行中的任务')),
  })
  const selectProject = (id: string) => {
    setSelectedProject(id)
    const p = projects.find((item) => item.id === id)
    if (p)
      form.setFieldsValue({
        ref: p.default_ref,
        vue_version: p.vue_version,
        install_strategy: p.install_strategy,
      })
  }
  const names = projectNameMap(projects)
  return (
    <div>
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>构建任务</Typography.Title>
          <Typography.Text type="secondary">触发、跟踪并下载 WGT 构建</Typography.Text>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            form.resetFields()
            setSelectedProject('')
            setOpen(true)
          }}
        >
          新建构建
        </Button>
      </div>
      <Card className="content-card">
        <Table
          rowKey="id"
          loading={isLoading}
          dataSource={builds}
          onRow={(record) => ({ onDoubleClick: () => navigate(`/builds/${record.id}`) })}
          columns={[
            { title: '项目', dataIndex: 'project_id', render: (id) => names[id] || id.slice(0, 8) },
            { title: 'Ref', dataIndex: 'requested_ref' },
            {
              title: 'Commit',
              dataIndex: 'commit_sha',
              render: (value) =>
                value ? <Typography.Text code>{value.slice(0, 8)}</Typography.Text> : '—',
            },
            { title: 'Vue', dataIndex: 'vue_version', render: (value) => `Vue ${value}` },
            {
              title: '状态',
              dataIndex: 'status',
              render: (value: Build['status']) => (
                <Tag color={buildStatusColor[value]}>{value}</Tag>
              ),
            },
            { title: '创建时间', dataIndex: 'created_at', render: formatDate },
            {
              title: '操作',
              render: (_, build) => (
                <Button
                  type="text"
                  icon={<EyeOutlined />}
                  onClick={() => navigate(`/builds/${build.id}`)}
                >
                  详情
                </Button>
              ),
            },
          ]}
        />
      </Card>
      <Modal
        title="新建 WGT 构建"
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={create.isPending}
      >
        <Form form={form} layout="vertical" onFinish={(values) => create.mutate(values)}>
          <Form.Item name="project_id" label="项目" rules={[{ required: true }]}>
            <Select
              onChange={selectProject}
              options={projects
                .filter((p) => p.is_active)
                .map((p) => ({ value: p.id, label: p.name }))}
            />
          </Form.Item>
          <Form.Item name="ref" label="分支、Tag 或 Commit" rules={[{ required: true }]}>
            <AutoComplete
              allowClear
              placeholder={refsLoading ? '正在加载远程 Ref…' : '选择远程 Ref 或直接输入 Commit'}
              options={refs.map((item) => ({
                value: item.name,
                label: `${item.type === 'branch' ? '分支' : 'Tag'} · ${item.name}`,
              }))}
              filterOption={(input, option) =>
                String(option?.value || '')
                  .toLowerCase()
                  .includes(input.toLowerCase())
              }
            />
          </Form.Item>
          <div className="form-grid">
            <Form.Item name="vue_version" label="Vue 版本">
              <Select
                options={[
                  { value: '2', label: 'Vue 2' },
                  { value: '3', label: 'Vue 3' },
                ]}
              />
            </Form.Item>
            <Form.Item name="install_strategy" label="依赖安装">
              <Select
                options={['none', 'npm-ci', 'yarn-frozen', 'pnpm-frozen'].map((value) => ({
                  value,
                  label: value,
                }))}
              />
            </Form.Item>
          </div>
        </Form>
      </Modal>
    </div>
  )
}
