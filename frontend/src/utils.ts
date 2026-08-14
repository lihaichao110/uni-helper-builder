import dayjs from 'dayjs'
import type { BuildStatus, Project } from './types'

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
