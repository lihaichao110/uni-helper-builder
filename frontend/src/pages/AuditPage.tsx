import { useQuery } from '@tanstack/react-query'
import { Card, Table, Typography } from 'antd'
import { api } from '../api'
import { formatDate } from '../utils'

interface Audit {
  id: string
  user_id?: string
  action: string
  target_type?: string
  target_id?: string
  detail?: string
  created_at: string
}
export default function AuditPage() {
  const { data = [] } = useQuery({
    queryKey: ['audit'],
    queryFn: () => api.get<Audit[]>('/audit-logs').then((r) => r.data),
  })
  return (
    <div>
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>审计日志</Typography.Title>
          <Typography.Text type="secondary">关键管理和交付操作记录</Typography.Text>
        </div>
      </div>
      <Card className="content-card">
        <Table
          rowKey="id"
          dataSource={data}
          columns={[
            { title: '时间', dataIndex: 'created_at', render: formatDate },
            { title: '操作', dataIndex: 'action' },
            {
              title: '用户 ID',
              dataIndex: 'user_id',
              render: (value) => value?.slice(0, 8) || '系统',
            },
            {
              title: '对象',
              render: (_, row) =>
                row.target_type ? `${row.target_type} / ${row.target_id?.slice(0, 8)}` : '—',
            },
            { title: '详情', dataIndex: 'detail', ellipsis: true, render: (value) => value || '—' },
          ]}
        />
      </Card>
    </div>
  )
}
