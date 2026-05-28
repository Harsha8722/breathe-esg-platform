import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { emissionsApi } from '@/services/api'
import { ScopeBadge, SourceTypeBadge, EmissionsValue, SkeletonRow, EmptyState, Pagination } from '@/components/ui/Badges'
import { format } from 'date-fns'
import { safeNumber } from '@/utils/format'

export default function FlaggedRecordsPage() {
  const [page, setPage]     = useState(1)
  const [search, setSearch] = useState('')

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['flagged-records', page, search],
    queryFn: () => emissionsApi.list({
      suspicious_flag: true,
      search: search || undefined,
      page,
      page_size: 25,
      ordering: '-created_at',
    }),
  })

  const recordsRaw = (data?.data?.results || []) as any[]
  const records = recordsRaw.map((r: any) => ({
    ...r,
    suspicious_reasons: Array.isArray(r?.suspicious_reasons) ? r.suspicious_reasons : [],
    validation_errors: Array.isArray(r?.validation_errors) ? r.validation_errors : [],
  }))
  const pagination = data?.data

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Flagged Records</h1>
        <p className="text-slate-500 text-sm mt-1">Records flagged by the validation and anomaly detection engine</p>
      </div>

      {/* Error */}
      {isError && (
        <div className="alert-error">
          <span className="text-2xl flex-shrink-0">⚠️</span>
          <div className="flex-1">
            <div className="font-bold">Failed to load flagged records</div>
            <div className="text-sm mt-0.5">
              {(error as any)?.response?.data?.error?.message ||
                (error as any)?.message ||
                'The API request failed.'}
            </div>
            <div className="mt-3">
              <button className="btn-secondary" onClick={() => refetch()}>
                Retry
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Alert banner */}
      <div className="alert-warning">
        <span className="text-2xl flex-shrink-0">⚠️</span>
        <div>
          <div className="font-bold">Analyst attention required</div>
          <div className="text-sm mt-0.5">
            These records failed automated validation or were detected as statistical anomalies (Z-score &gt; 3σ).
            Review each individually before approving or rejecting.
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="card p-4">
        <input
          type="search" value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          placeholder="Search flagged records by location, vendor, source ID..."
          className="input-field"
        />
      </div>

      {/* Stats chips */}
      {pagination && (
        <div className="flex items-center gap-3">
          <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-2.5 flex items-center gap-2">
            <span className="text-2xl font-bold text-red-700">{pagination.count}</span>
            <span className="text-sm font-medium text-red-600">total flagged records</span>
          </div>
          <div className="text-slate-400 text-sm">
            Review and resolve each item to keep your dataset clean.
            {isFetching && <span className="ml-2 text-xs text-ocean-600 font-semibold">Refreshing…</span>}
          </div>
        </div>
      )}

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="tbl-wrap">
          <table className="tbl">
            <thead>
              <tr>
                <th>Date</th>
                <th>Source</th>
                <th>Scope</th>
                <th>Location</th>
                <th>Quantity</th>
                <th>Emissions</th>
                <th>Flag Reasons</th>
                <th>Validation Errors</th>
              </tr>
            </thead>
            <tbody>
              {isLoading
                ? [...Array(6)].map((_, i) => <SkeletonRow key={i} cols={8} />)
                : records.length === 0
                  ? <tr><td colSpan={8}><EmptyState message="No flagged records — the data pipeline is clean! 🎉" icon="✅" /></td></tr>
                  : records.map((r) => (
                      <tr key={r.id}>
                        <td className="font-mono text-xs font-medium text-slate-600 whitespace-nowrap">
                          {r.activity_date ? format(new Date(r.activity_date), 'MMM d, yyyy') : '—'}
                        </td>
                        <td><SourceTypeBadge type={r.source_type} /></td>
                        <td><ScopeBadge scope={r.scope_category} /></td>
                        <td className="text-slate-700 font-medium">{r.location || '—'}</td>
                        <td className="font-mono text-sm font-medium text-slate-700">
                          {r.normalized_quantity != null ? safeNumber(r.normalized_quantity).toFixed(2) : '—'}
                          <span className="text-slate-400 ml-1 text-xs">{r.normalized_unit}</span>
                        </td>
                        <td><EmissionsValue value={r.calculated_emissions} /></td>
                        <td className="min-w-[220px]">
                          <div className="space-y-1">
                            {r.suspicious_reasons.slice(0, 2).map((reason: string, i: number) => (
                              <div key={i}
                                className="text-xs text-red-700 bg-red-50 border border-red-200 rounded-lg px-2 py-1 font-medium">
                                {reason.length > 65 ? reason.slice(0, 65) + '…' : reason}
                              </div>
                            ))}
                            {r.suspicious_reasons.length > 2 && (
                              <div className="text-xs text-red-500 font-medium">
                                +{r.suspicious_reasons.length - 2} more flags
                              </div>
                            )}
                            {r.suspicious_reasons.length === 0 && (
                              <span className="text-xs text-slate-500 font-medium bg-slate-50 border border-slate-200 rounded-lg px-2 py-1">
                                No flag reasons provided
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="min-w-[180px]">
                          <div className="space-y-1">
                            {r.validation_errors.slice(0, 2).map((err: string, i: number) => (
                              <div key={i}
                                className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-2 py-1 font-medium">
                                {err}
                              </div>
                            ))}
                            {r.validation_errors.length === 0 && (
                              <span className="text-xs text-teal-600 font-medium bg-teal-50 border border-teal-200 rounded-lg px-2 py-1">
                                No validation errors
                              </span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
              }
            </tbody>
          </table>
        </div>
        {pagination && pagination.total_pages > 1 && (
          <Pagination
            current={pagination.current_page} total={pagination.total_pages} count={pagination.count}
            onPrev={() => setPage((p) => Math.max(1, p - 1))} onNext={() => setPage((p) => p + 1)}
          />
        )}
      </div>
    </div>
  )
}
