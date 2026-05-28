// API types for Breathe ESG Platform

export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  full_name: string
  role: 'admin' | 'analyst' | 'reviewer' | 'viewer'
  tenant: Tenant | null
  is_active: boolean
  created_at: string
}

export interface Tenant {
  id: string
  name: string
  slug: string
  plan: 'starter' | 'professional' | 'enterprise'
  industry: string
  country: string
  reporting_year: number
  user_count?: number
}

export interface AuthTokens {
  access: string
  refresh: string
  user: User
}

export type SourceType = 'sap_fuel' | 'utility_electricity' | 'corporate_travel'
export type RecordStatus = 'pending' | 'flagged' | 'approved' | 'rejected' | 'locked'
export type ScopeCategory = 'scope_1' | 'scope_2' | 'scope_3'

export interface SourceFile {
  id: string
  source_type: SourceType
  original_filename: string
  file_size_bytes: number
  status: 'pending' | 'processing' | 'processed' | 'failed'
  total_rows: number
  processed_rows: number
  flagged_rows: number
  failed_rows: number
  success_rate: number
  ingestion_timestamp: string
  processing_started_at: string | null
  processing_completed_at: string | null
  error_message: string
  uploaded_by_name: string | null
}

export interface EmissionRecord {
  id: string
  status: RecordStatus
  scope_category: ScopeCategory
  activity_category: string
  source_type: SourceType
  activity_date: string | null
  quantity: number | null
  raw_unit: string
  normalized_quantity: number | null
  normalized_unit: string
  calculated_emissions: number | null
  calculated_emissions_unit: string
  suspicious_flag: boolean
  is_duplicate: boolean
  source_identifier: string
  location: string
  vendor: string
  analyst_notes: string
  validation_errors: string[]
  suspicious_reasons: string[]
  approved_by_name: string | null
  reviewed_by_name: string | null
  approved_at: string | null
  reviewed_at: string | null
  created_at: string
  row_number: number
  // Detail fields
  emission_factor?: number | null
  emission_factor_source?: string
  cost_center?: string
  original_payload?: Record<string, unknown>
  locked_at?: string | null
  rejected_reason?: string
}

export interface EmissionsSummary {
  total_records: number
  pending: number
  flagged: number
  approved: number
  rejected: number
  locked: number
  total_scope1_kgco2e: number
  total_scope2_kgco2e: number
  total_scope3_kgco2e: number
  total_emissions_kgco2e: number
}

export interface AuditLog {
  id: string
  action: string
  target_type: string
  target_id: string
  target_repr: string
  before_state: Record<string, unknown>
  after_state: Record<string, unknown>
  metadata: Record<string, unknown>
  notes: string
  actor_name: string
  ip_address: string | null
  timestamp: string
}

export interface PaginatedResponse<T> {
  count: number
  total_pages: number
  current_page: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface ApiResponse<T> {
  success: boolean
  data: T
  message?: string
}

export interface EmissionFilters {
  status?: RecordStatus[]
  scope_category?: ScopeCategory[]
  source_type?: string
  suspicious_flag?: boolean
  date_from?: string
  date_to?: string
  source_file?: string
  search?: string
  page?: number
  page_size?: number
  ordering?: string
}
