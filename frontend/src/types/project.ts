export type InstallStrategy = 'none' | 'npm-ci' | 'yarn-frozen' | 'pnpm-frozen'

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
