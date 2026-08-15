export interface Credential {
  id: string
  name: string
  type: 'ssh' | 'https-token'
  username?: string
  known_hosts?: string
  created_at: string
}
