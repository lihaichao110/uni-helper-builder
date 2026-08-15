import { isAxiosError } from 'axios'

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
