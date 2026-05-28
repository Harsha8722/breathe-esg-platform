import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

/**
 * Serialize params so Django receives array filters correctly.
 * Axios 1.x defaults to `key[]=val` but Django MultipleChoiceFilter
 * expects repeated keys: `status=pending&status=flagged`
 */
function serializeParams(params: Record<string, unknown>): string {
  const parts: string[] = []
  for (const key of Object.keys(params)) {
    const val = params[key]
    if (val === undefined || val === null) continue
    if (Array.isArray(val)) {
      val.forEach((v) => {
        if (v !== undefined && v !== null) {
          parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(v))}`)
        }
      })
    } else if (typeof val === 'boolean') {
      parts.push(`${encodeURIComponent(key)}=${val ? 'true' : 'false'}`)
    } else {
      parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(val))}`)
    }
  }
  return parts.join('&')
}

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  paramsSerializer: serializeParams as any,
})

// Request interceptor — attach JWT + tenant header
apiClient.interceptors.request.use((config) => {
  const { tokens, user } = useAuthStore.getState()
  if (tokens?.access) {
    config.headers.Authorization = `Bearer ${tokens.access}`
  }
  if (user?.tenant?.id) {
    config.headers['X-Tenant-ID'] = user.tenant.id
  }
  return config
})

// Response interceptor — handle 401 and auto-refresh token
apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const { tokens, setTokens, logout } = useAuthStore.getState()
      if (tokens?.refresh) {
        try {
          const res = await axios.post(`${BASE_URL}/auth/token/refresh/`, {
            refresh: tokens.refresh,
          })
          const newAccess = res.data.access
          setTokens({ ...tokens, access: newAccess })
          original.headers.Authorization = `Bearer ${newAccess}`
          return apiClient(original)
        } catch {
          logout()
        }
      } else {
        logout()
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient
