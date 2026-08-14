import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import type { User } from './types'

let accessToken = ''
let refreshPromise: Promise<string> | null = null
export const API_BASE = import.meta.env.DEV ? 'http://127.0.0.1:8000/api' : '/api'

export const api = axios.create({ baseURL: API_BASE, withCredentials: true })

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
