import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Card, Descriptions, Result, Space, Spin, Steps, Tag, Typography } from 'antd'
import { ArrowLeftOutlined, DownloadOutlined, StopOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import { API_BASE, api, getAccessToken } from '../../api'
import { ACTIVE_BUILD_STATUSES, buildStatusColor } from '../../constants/build'
import type { Build } from '../../types/build'
import type { Project } from '../../types/project'
import { formatDate, bytes } from '../../utils/format'
import { extractErrorMessage } from '../../utils/error'

const stages = ['queued', 'cloning', 'installing', 'building', 'packaging', 'succeeded']

export default function BuildDetailPage() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { message } = App.useApp()
  const [logs, setLogs] = useState('')
  const terminalRef = useRef<HTMLPreElement>(null)
  const { data: build, isLoading } = useQuery({
    queryKey: ['build', id],
    queryFn: () => api.get<Build>(`/builds/${id}`).then((r) => r.data),
    refetchInterval: 2500,
  })
  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.get<Project[]>('/projects').then((r) => r.data),
  })
  const cancel = useMutation({
    mutationFn: () => api.post(`/builds/${id}/cancel`),
    onSuccess: () => {
      message.success('取消请求已提交')
      queryClient.invalidateQueries({ queryKey: ['build', id] })
    },
    onError: (error) => message.error(extractErrorMessage(error, '当前任务无法取消')),
  })
  useEffect(() => {
    let socket: WebSocket | undefined
    let closed = false
    api.get<{ content: string; offset: number }>(`/builds/${id}/logs`).then(({ data }) => {
      if (closed) return
      setLogs(data.content)
      const apiUrl = new URL(API_BASE, window.location.origin)
      const protocol = apiUrl.protocol === 'https:' ? 'wss:' : 'ws:'
      socket = new WebSocket(
        `${protocol}//${apiUrl.host}${apiUrl.pathname}/builds/${id}/logs/stream?token=${encodeURIComponent(getAccessToken())}&offset=${data.offset}`,
      )
      socket.onmessage = (event) => setLogs((value) => value + event.data)
    })
    return () => {
      closed = true
      socket?.close()
    }
  }, [id])
  useEffect(() => {
    if (terminalRef.current) terminalRef.current.scrollTop = terminalRef.current.scrollHeight
  }, [logs])
  if (isLoading || !build)
    return (
      <div className="center-content">
        <Spin />
      </div>
    )
  const project = projects.find((p) => p.id === build.project_id)
  const current =
    build.status === 'failed' || build.status === 'canceled'
      ? stages.indexOf('building')
      : Math.max(0, stages.indexOf(build.status))
  const active = ACTIVE_BUILD_STATUSES.has(build.status)
  const download = async () => {
    if (!build.artifact) return
    const response = await api.get(`/artifacts/${build.artifact.id}/download`, {
      responseType: 'blob',
    })
    const url = URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = url
    link.download = build.artifact.filename
    link.click()
    URL.revokeObjectURL(url)
  }
  return (
    <div>
      <div className="page-heading">
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/builds')} />
          <div>
            <Typography.Title level={2}>{project?.name || '构建详情'}</Typography.Title>
            <Typography.Text type="secondary">任务 {build.id}</Typography.Text>
          </div>
        </Space>
        <Space>
          {active && (
            <Button
              danger
              icon={<StopOutlined />}
              loading={cancel.isPending}
              onClick={() => cancel.mutate()}
            >
              取消构建
            </Button>
          )}
          {build.artifact && (
            <Button type="primary" icon={<DownloadOutlined />} onClick={download}>
              下载 WGT
            </Button>
          )}
        </Space>
      </div>
      <Card className="content-card build-overview">
        <Space size="large" align="start" wrap>
          <Tag color={buildStatusColor[build.status]} className="large-status">
            {build.status}
          </Tag>
          <Descriptions
            column={{ xs: 1, sm: 2, lg: 4 }}
            items={[
              { key: 'ref', label: 'Ref', children: build.requested_ref },
              {
                key: 'commit',
                label: 'Commit',
                children: build.commit_sha?.slice(0, 12) || '等待检出',
              },
              {
                key: 'vue',
                label: '构建链',
                children: `Vue ${build.vue_version} / ${build.install_strategy}`,
              },
              { key: 'created', label: '创建时间', children: formatDate(build.created_at) },
            ]}
          />
        </Space>
        <Steps
          current={current}
          status={
            build.status === 'failed' ? 'error' : build.status === 'canceled' ? 'error' : 'process'
          }
          className="build-steps"
          items={['排队', '拉取代码', '安装依赖', '编译', '打包', '完成'].map((title) => ({
            title,
          }))}
        />
      </Card>
      {(build.error_summary || build.artifact) && (
        <Card className="content-card section-row">
          {build.error_summary ? (
            <Result
              status={build.status === 'canceled' ? 'warning' : 'error'}
              title={build.error_summary}
              subTitle={build.error_code}
            />
          ) : (
            build.artifact && (
              <Descriptions
                title="构建产物"
                items={[
                  { key: 'name', label: '文件名', children: build.artifact.filename },
                  { key: 'size', label: '大小', children: bytes(build.artifact.size_bytes) },
                  {
                    key: 'sha',
                    label: 'SHA-256',
                    children: (
                      <Typography.Text copyable code>
                        {build.artifact.sha256}
                      </Typography.Text>
                    ),
                  },
                ]}
              />
            )
          )}
        </Card>
      )}
      <Card
        title="实时日志"
        className="content-card section-row"
        extra={
          active && (
            <Space>
              <Spin size="small" />
              实时更新
            </Space>
          )
        }
      >
        <pre ref={terminalRef} className="terminal">
          {logs || '等待日志输出…'}
        </pre>
      </Card>
    </div>
  )
}
