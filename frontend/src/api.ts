import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import type { User } from './types/user'

let accessToken = ''
let refreshPromise: Promise<string> | null = null
// 始终走同源相对路径：开发环境由 vite proxy 转发到 127.0.0.1:8000，生产由 nginx 反代 /api。
// 这样 refresh_token Cookie 与页面同源，不会被浏览器的跨站 Cookie 策略拦截。
export const API_BASE = '/api'

export const api = axios.create({ baseURL: API_BASE, withCredentials: true, timeout: 60000 })

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})

async function refreshAccessToken(): Promise<string> {
  const response = await axios.post<{ access_token: string; user: User }>(
    `${API_BASE}/auth/refresh`,
    {},
    { withCredentials: true },
  )
  accessToken = response.data.access_token
  return accessToken
}

api.interceptors.response.use(undefined, async (error: AxiosError) => {
  const config = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined
  if (
    error.response?.status === 401 &&
    config &&
    !config._retried &&
    !config.url?.includes('/auth/')
  ) {
    config._retried = true
    refreshPromise ??= refreshAccessToken().finally(() => {
      refreshPromise = null
    })
    const token = await refreshPromise
    config.headers.Authorization = `Bearer ${token}`
    return api(config)
  }
  throw error
})

export function setAccessToken(token: string) {
  accessToken = token
}
export function getAccessToken() {
  return accessToken
}

export async function bootstrapSession(): Promise<User | null> {
  try {
    const response = await axios.post<{ access_token: string; user: User }>(
      `${API_BASE}/auth/refresh`,
      {},
      { withCredentials: true },
    )
    accessToken = response.data.access_token
    return response.data.user
  } catch {
    return null
  }
}
