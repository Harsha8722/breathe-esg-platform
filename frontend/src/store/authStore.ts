import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, AuthTokens } from '@/types'

interface AuthState {
  user: User | null
  tokens: { access: string; refresh: string } | null
  isAuthenticated: boolean
  setAuth: (tokens: AuthTokens) => void
  setTokens: (tokens: { access: string; refresh: string }) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      tokens: null,
      isAuthenticated: false,
      setAuth: ({ access, refresh, user }) => set({
        tokens: { access, refresh },
        user,
        isAuthenticated: true,
      }),
      setTokens: (tokens) => set({ tokens, isAuthenticated: Boolean(tokens?.access) }),
      logout: () => set({ user: null, tokens: null, isAuthenticated: false }),
    }),
    {
      name: 'breathe-auth',
      partialize: (state) => ({ user: state.user, tokens: state.tokens, isAuthenticated: state.isAuthenticated }),
      onRehydrateStorage: () => (state) => {
        // Ensure private routes don't flicker to /login after refresh when tokens exist.
        const access = state?.tokens?.access
        if (access) {
          useAuthStore.setState({ isAuthenticated: true })
        }
      },
    }
  )
)
