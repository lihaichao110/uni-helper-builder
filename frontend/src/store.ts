import { create } from 'zustand'
import type { User } from './types'

interface AuthState {
  user: User | null
  bootstrapped: boolean
  setUser: (user: User | null) => void
  setBootstrapped: (value: boolean) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  bootstrapped: false,
  setUser: (user) => set({ user }),
  setBootstrapped: (bootstrapped) => set({ bootstrapped }),
}))
