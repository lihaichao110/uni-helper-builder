export type Role = 'admin' | 'member'
export type InstallStrategy = 'none' | 'npm-ci' | 'yarn-frozen' | 'pnpm-frozen'
export type BuildStatus =
  | 'queued'
  | 'cloning'
  | 'installing'
  | 'building'
  | 'packaging'
  | 'succeeded'
  | 'failed'
  | 'canceling'
  | 'canceled'

export interface User {
  id: string
  username: string
  role: Role
  is_active: boolean
  last_login_at?: string
  created_at: string
}
export interface Credential {
  id: string
  name: string
  type: 'ssh' | 'https-token'
  username?: string
  known_hosts?: string
  created_at: string
}
export interface Project {
  id: string
  name: string
  git_url: string
  default_ref: string
  vue_version: '2' | '3'
  install_strategy: InstallStrategy
  node_memory_mb: number
  timeout_minutes: number
  is_active: boolean
  credential_id?: string
  created_at: string
  updated_at: string
}
export interface Artifact {
  id: string
  filename: string
  size_bytes: number
  sha256: string
  created_at: string
}
export interface Build {
  id: string
  project_id: string
  requested_by_id: string
  requested_ref: string
  commit_sha?: string
  vue_version: '2' | '3'
  install_strategy: InstallStrategy
  status: BuildStatus
  error_code?: string
  error_summary?: string
  started_at?: string
  finished_at?: string
  created_at: string
  updated_at: string
  cancel_requested: boolean
  artifact?: Artifact
}
