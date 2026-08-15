export type Role = 'admin' | 'member'

export interface User {
  id: string
  username: string
  role: Role
  is_active: boolean
  last_login_at?: string
  created_at: string
}
