import { apiClient } from './apiClient'
import type {
  AuthTokens, EmissionRecord, EmissionsSummary, EmissionFilters,
  SourceFile, AuditLog, PaginatedResponse, ApiResponse
} from '@/types'

// Auth
export const authApi = {
  login: (email: string, password: string) =>
    apiClient.post<ApiResponse<AuthTokens>>('/auth/login/', { email, password }),
  register: (
    first_name: string, last_name: string,
    email: string, password: string,
    confirm_password: string, role: string
  ) =>
    apiClient.post<ApiResponse<AuthTokens>>('/auth/register/', {
      first_name, last_name, email, password, confirm_password, role,
    }),
  logout: (refresh: string) =>
    apiClient.post('/auth/logout/', { refresh }),
  me: () => apiClient.get<ApiResponse<AuthTokens['user']>>('/auth/me/'),
  refreshToken: (refresh: string) =>
    apiClient.post('/auth/token/refresh/', { refresh }),
}

// Emissions
export const emissionsApi = {
  list: (filters: EmissionFilters = {}) =>
    apiClient.get<PaginatedResponse<EmissionRecord>>('/emissions/records/', { params: filters }),
  detail: (id: string) =>
    apiClient.get<ApiResponse<EmissionRecord>>(`/emissions/records/${id}/`),
  review: (id: string, action: string, notes?: string, rejectedReason?: string) =>
    apiClient.post<ApiResponse<EmissionRecord>>(`/emissions/records/${id}/review/`, {
      action, notes, rejected_reason: rejectedReason
    }),
  bulkAction: (recordIds: string[], action: string, notes?: string) =>
    apiClient.post('/emissions/records/bulk-action/', { record_ids: recordIds, action, notes }),
  summary: () =>
    apiClient.get<ApiResponse<EmissionsSummary>>('/emissions/summary/'),
}

// Ingestion
export const ingestionApi = {
  list: (params?: Record<string, string>) =>
    apiClient.get<ApiResponse<SourceFile[]>>('/ingestion/uploads/', { params }),
  upload: (file: File, sourceType: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('source_type', sourceType)
    return apiClient.post<ApiResponse<SourceFile>>('/ingestion/uploads/upload/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  detail: (id: string) =>
    apiClient.get<ApiResponse<SourceFile>>(`/ingestion/uploads/${id}/`),
}

// Audit
export const auditApi = {
  list: (params?: Record<string, string | number>) =>
    apiClient.get<PaginatedResponse<AuditLog>>('/audit/logs/', { params }),
}

// Analytics
export const analyticsApi = {
  scopeTrend: (year?: string) =>
    apiClient.get('/analytics/scope-trend/', { params: { year } }),
  sourceBreakdown: () =>
    apiClient.get('/analytics/source-breakdown/'),
  ingestionStats: () =>
    apiClient.get('/analytics/ingestion-stats/'),
}
