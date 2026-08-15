import { ACTIVE_BUILD_STATUSES } from '../constants/build'
import type { Build } from '../types/build'
import type { Project } from '../types/project'

/** ['builds'] 列表查询的轮询间隔：存在活跃任务时每 5 秒刷新，否则停止轮询 */
export const buildsRefetchInterval = (query: { state: { data?: Build[] } }) =>
  (query.state.data ?? []).some((b) => ACTIVE_BUILD_STATUSES.has(b.status)) ? 5000 : false

export const projectNameMap = (projects: Project[]) =>
  Object.fromEntries(projects.map((p) => [p.id, p.name]))
