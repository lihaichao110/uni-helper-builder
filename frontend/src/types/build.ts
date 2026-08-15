import type { InstallStrategy } from './project'

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
