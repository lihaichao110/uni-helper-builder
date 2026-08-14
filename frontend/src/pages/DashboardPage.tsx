import { useQuery } from '@tanstack/react-query'
import { Card, Col, Progress, Row, Space, Statistic, Table, Tag, Typography } from 'antd'
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
} from '@ant-design/icons'
import { api } from '../api'
import type { Build, Project } from '../types'
import { buildStatusColor, formatDate, projectNameMap } from '../utils'

export default function DashboardPage() {
  const { data: builds = [] } = useQuery({
    queryKey: ['builds'],
    queryFn: () => api.get<Build[]>('/builds').then((r) => r.data),
    refetchInterval: 5000,
  })
  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.get<Project[]>('/projects').then((r) => r.data),
  })
  const succeeded = builds.filter((b) => b.status === 'succeeded').length
  const failed = builds.filter((b) => b.status === 'failed').length
  const running = builds.filter((b) =>
    ['cloning', 'installing', 'building', 'packaging'].includes(b.status),
  ).length
  const rate = succeeded + failed ? Math.round((succeeded / (succeeded + failed)) * 100) : 0
  const names = projectNameMap(projects)
  return (
    <div>
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>构建概览</Typography.Title>
          <Typography.Text type="secondary">掌握项目交付状态和最近活动</Typography.Text>
        </div>
      </div>
      <Row gutter={[18, 18]}>
        <Col xs={24} sm={12} xl={6}>
          <Card className="metric-card">
            <Statistic
              title="排队任务"
              value={builds.filter((b) => b.status === 'queued').length}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card className="metric-card">
            <Statistic
              title="运行中"
              value={running}
              prefix={<SyncOutlined spin={running > 0} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card className="metric-card">
            <Statistic title="成功构建" value={succeeded} prefix={<CheckCircleOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card className="metric-card">
            <Statistic title="失败构建" value={failed} prefix={<CloseCircleOutlined />} />
          </Card>
        </Col>
      </Row>
      <Row gutter={[18, 18]} className="section-row">
        <Col xs={24} lg={16}>
          <Card title="最近构建" className="content-card">
            <Table
              rowKey="id"
              dataSource={builds.slice(0, 8)}
              pagination={false}
              size="middle"
              columns={[
                {
                  title: '项目',
                  dataIndex: 'project_id',
                  render: (id) => names[id] || id.slice(0, 8),
                },
                { title: 'Ref', dataIndex: 'requested_ref' },
                {
                  title: '状态',
                  dataIndex: 'status',
                  render: (value: Build['status']) => (
                    <Tag color={buildStatusColor[value]}>{value}</Tag>
                  ),
                },
                { title: '创建时间', dataIndex: 'created_at', render: formatDate },
              ]}
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="交付健康度" className="content-card health-card">
            <Progress type="dashboard" percent={rate} strokeColor="#5b7cfa" />
            <Space direction="vertical" align="center">
              <Typography.Text strong>最近 {succeeded + failed} 次已完成构建</Typography.Text>
              <Typography.Text type="secondary">当前管理 {projects.length} 个项目</Typography.Text>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
