import dayjs from 'dayjs'
import { isAxiosError } from 'axios'
import type { Build, BuildStatus, Project } from './types'

/** 活跃（非终态）构建状态集合，需与后端 ACTIVE_BUILD_STATUSES 保持一致 */
export const ACTIVE_BUILD_STATUSES: ReadonlySet<BuildStatus> = new Set([
  'queued',
  'cloning',
  'installing',
  'building',
  'packaging',
  'canceling',
])

/** ['builds'] 列表查询的轮询间隔：存在活跃任务时每 5 秒刷新，否则停止轮询 */
export const buildsRefetchInterval = (query: { state: { data?: Build[] } }) =>
  (query.state.data ?? []).some((b) => ACTIVE_BUILD_STATUSES.has(b.status)) ? 5000 : false

export const buildStatusColor: Record<BuildStatus, string> = {
  queued: 'default',
  cloning: 'processing',
  installing: 'processing',
  building: 'blue',
  packaging: 'purple',
  succeeded: 'success',
  failed: 'error',
  canceling: 'warning',
  canceled: 'default',
}
export const formatDate = (value?: string) =>
  value ? dayjs(value).format('YYYY-MM-DD HH:mm:ss') : '—'
export const projectNameMap = (projects: Project[]) =>
  Object.fromEntries(projects.map((p) => [p.id, p.name]))
export const bytes = (value: number) =>
  value > 1024 * 1024 ? `${(value / 1024 / 1024).toFixed(2)} MB` : `${(value / 1024).toFixed(1)} KB`

/** FastAPI 422 参数校验错误项（形如 { loc: ['body', 'name'], msg: '...' }） */
interface ValidationIssue {
  loc?: (string | number)[]
  msg?: string
}

/**
 * 从 Axios 错误中提取后端返回的可读错误信息（error.response.data.detail），
 * 兼容 detail 为字符串或 FastAPI 422 校验错误数组的情况；
 * 网络错误、超时或无可用 detail 时回退到默认文案。
 */
export function extractErrorMessage(error: unknown, fallback = '请求失败，请稍后重试'): string {
  if (!isAxiosError(error)) return fallback
  const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item): string => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object') {
          const issue = item as ValidationIssue
          const field = issue.loc?.filter((part) => part !== 'body').join('.')
          const msg = issue.msg?.trim()
          if (msg) return field ? `${field}: ${msg}` : msg
        }
        return ''
      })
      .filter(Boolean)
    if (messages.length > 0) return messages.join('；')
  }
  return fallback
}
