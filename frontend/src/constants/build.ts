import type { BuildStatus } from '../types/build'

/** 活跃（非终态）构建状态集合，需与后端 ACTIVE_BUILD_STATUSES 保持一致 */
export const ACTIVE_BUILD_STATUSES: ReadonlySet<BuildStatus> = new Set([
  'queued',
  'cloning',
  'installing',
  'building',
  'packaging',
  'canceling',
])

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
