import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { emissionsApi } from '@/services/api'
import {
  StatusBadge, ScopeBadge, SourceTypeBadge, SuspiciousIndicator,
  EmissionsValue, SkeletonRow, EmptyState, Pagination,
} from '@/components/ui/Badges'
import { format } from 'date-fns'
import { safeNumber } from '@/utils/format'
import type { EmissionRecord, RecordStatus } from '@/types'

const STATUS_OPTS: { value: RecordStatus | ''; label: string }[] = [
  { value: '', label: 'All Statuses' },
  { value: 'pending',  label: '⏳ Pending'  },
  { value: 'flagged',  label: '🚩 Flagged'  },
  { value: 'approved', label: '✅ Approved' },
  { value: 'rejected', label: '❌ Rejected' },
  { value: 'locked',   label: '🔒 Locked'   },
]

/* ─── Review Modal ─── */
function ReviewModal({ record, onClose }: { record: EmissionRecord; onClose: () => void }) {
  const [action, setAction] = useState<'approve' | 'reject' | 'note' | 'flag'>('note')
  const [notes, setNotes]   = useState(record.analyst_notes || '')
  const qc = useQueryClient()

  const reviewMutation = useMutation({
    mutationFn: () => emissionsApi.review(record.id, action, notes),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['emission-records'] })
      qc.invalidateQueries({ queryKey: ['emissions-summary'] })
      onClose()
    },
  })

  const actions = [
    { value: 'approve', label: '✅ Approve', cls: 'bg-teal-600 text-white border-teal-600 hover:bg-teal-700', active: 'bg-teal-600 text-white border-teal-600' },
    { value: 'reject',  label: '❌ Reject',  cls: 'bg-red-600 text-white border-red-600 hover:bg-red-700',   active: 'bg-red-600 text-white border-red-600' },
    { value: 'flag',    label: '🚩 Flag',    cls: 'bg-amber-500 text-white border-amber-500 hover:bg-amber-600', active: 'bg-amber-500 text-white border-amber-500' },
    { value: 'note',    label: '📝 Note',    cls: 'bg-ocean-600 text-white border-ocean-600 hover:bg-ocean-700', active: 'bg-ocean-600 text-white border-ocean-600' },
  ]

  return (
    <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-modal w-full max-w-2xl max-h-[90vh] overflow-y-auto animate-slide-up">

        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-100 flex items-start justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-800">Review Emission Record</h2>
            <p className="text-xs text-slate-400 font-mono mt-1">{record.id.slice(0, 16)}...</p>
          </div>
          <button onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-500 hover:text-slate-700 transition-colors">
            ✕
          </button>
        </div>

        <div className="p-6 space-y-5">
          {/* Details grid */}
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'Status',     node: <StatusBadge status={record.status} /> },
              { label: 'Scope',      node: <ScopeBadge scope={record.scope_category} /> },
              { label: 'Source',     node: <SourceTypeBadge type={record.source_type} /> },
              { label: 'Date',       node: record.activity_date ? format(new Date(record.activity_date), 'MMM d, yyyy') : '—' },
              { label: 'Quantity',   node: record.normalized_quantity != null ? `${safeNumber(record.normalized_quantity).toFixed(2)} ${record.normalized_unit || ''}`.trim() : '—' },
              { label: 'Emissions',  node: <EmissionsValue value={record.calculated_emissions} /> },
              { label: 'Location',   node: record.location || '—' },
              { label: 'Vendor',     node: record.vendor || '—' },
              { label: 'Source ID',  node: <span className="font-mono text-xs">{record.source_identifier || '—'}</span> },
              { label: 'Row #',      node: record.row_number },
            ].map(({ label, node }) => (
              <div key={label} className="bg-slate-50 border border-slate-100 rounded-xl p-3">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1">{label}</div>
                <div className="text-sm font-medium text-slate-800">{node as any}</div>
              </div>
            ))}
          </div>

          {/* Suspicious */}
          {record.suspicious_flag && (record.suspicious_reasons || []).length > 0 && (
            <div className="alert-error">
              <span className="text-xl flex-shrink-0">⚠️</span>
              <div>
                <div className="font-bold text-sm mb-1">Suspicious Flags Detected</div>
                <ul className="space-y-0.5">
                  {record.suspicious_reasons.map((r, i) => (
                    <li key={i} className="text-xs">{r}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Validation errors */}
          {(record.validation_errors || []).length > 0 && (
            <div className="alert-warning">
              <span className="text-xl flex-shrink-0">⚡</span>
              <div>
                <div className="font-bold text-sm mb-1">Validation Errors</div>
                <ul className="space-y-0.5">
                  {(record.validation_errors || []).map((e, i) => <li key={i} className="text-xs">{e}</li>)}
                </ul>
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div>
            <div className="text-sm font-bold text-slate-700 mb-2">Select Action</div>
            <div className="flex flex-wrap gap-2">
              {actions.map((a) => (
                <button
                  key={a.value}
                  onClick={() => setAction(a.value as any)}
                  className={`px-4 py-2 rounded-xl border-2 font-semibold text-sm transition-all ${
                    action === a.value ? a.active : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
                  }`}
                >
                  {a.label}
                </button>
              ))}
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="input-label">Analyst Notes</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="input-field resize-none h-24"
              placeholder="Document your analysis, data verification, or rejection reason..."
            />
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100 flex gap-3 justify-end bg-slate-50/50 rounded-b-3xl">
          <button onClick={onClose} className="btn-ghost">Cancel</button>
          <button onClick={() => reviewMutation.mutate()} disabled={reviewMutation.isPending} className="btn-primary">
            {reviewMutation.isPending ? 'Saving...' : `Submit — ${action.charAt(0).toUpperCase() + action.slice(1)}`}
          </button>
        </div>
      </div>
    </div>
  )
}

/* ─── Review Queue Page ─── */
export default function ReviewQueuePage() {
  const [statusFilter, setStatusFilter] = useState<RecordStatus | ''>('pending')
  const [search, setSearch]             = useState('')
  const [page, setPage]                 = useState(1)
  const [selectedRecord, setSelectedRecord] = useState<EmissionRecord | null>(null)
  const [selectedIds, setSelectedIds]   = useState<Set<string>>(new Set())
  const qc = useQueryClient()

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['emission-records', statusFilter, search, page],
    queryFn: () => emissionsApi.list({
      status: statusFilter ? [statusFilter] : undefined,
      search: search || undefined,
      page,
      page_size: 25,
    }),
  })

  const bulkMutation = useMutation({
    mutationFn: (action: string) => emissionsApi.bulkAction([...selectedIds], action),
    onSuccess: () => {
      setSelectedIds(new Set())
      qc.invalidateQueries({ queryKey: ['emission-records'] })
      qc.invalidateQueries({ queryKey: ['emissions-summary'] })
    },
  })

  const recordsRaw = (data?.data?.results || []) as any[]
  const records: EmissionRecord[] = recordsRaw.map((r: any) => ({
    ...r,
    suspicious_reasons: Array.isArray(r?.suspicious_reasons) ? r.suspicious_reasons : [],
    validation_errors: Array.isArray(r?.validation_errors) ? r.validation_errors : [],
  }))
  const pagination = data?.data

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n })
  }

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Review Queue</h1>
          <p className="text-slate-500 text-sm mt-1">Review, approve, or reject ingested ESG records</p>
        </div>
        {selectedIds.size > 0 && (
          <div className="flex gap-2">
            <button onClick={() => bulkMutation.mutate('approve')} disabled={bulkMutation.isPending}
              className="btn-teal text-sm">✅ Approve {selectedIds.size}</button>
            <button onClick={() => bulkMutation.mutate('reject')} disabled={bulkMutation.isPending}
              className="btn-danger text-sm">❌ Reject {selectedIds.size}</button>
          </div>
        )}
      </div>

      {/* Error */}
      {isError && (
        <div className="alert-error">
          <span className="text-2xl flex-shrink-0">⚠️</span>
          <div className="flex-1">
            <div className="font-bold">Failed to load review queue</div>
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

      {/* Filters */}
      <div className="card p-4 flex flex-wrap gap-3">
        <input
          type="search" value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          placeholder="Search by location, vendor, source ID..."
          className="input-field flex-1 min-w-52"
        />
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value as any); setPage(1) }}
          className="input-field w-44"
        >
          {STATUS_OPTS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        {isFetching && (
          <div className="flex items-center gap-2 text-xs font-semibold text-ocean-700 bg-ocean-50 border border-ocean-200 rounded-xl px-3 py-2">
            <span className="w-3 h-3 border-2 border-ocean-300 border-t-ocean-600 rounded-full animate-spin" />
            Refreshing
          </div>
        )}
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="tbl-wrap">
          <table className="tbl">
            <thead>
              <tr>
                <th className="w-10">
                  <input type="checkbox" className="rounded border-slate-300"
                    onChange={(e) => {
                      if (e.target.checked) setSelectedIds(new Set(records.map((r) => r.id)))
                      else setSelectedIds(new Set())
                    }}
                  />
                </th>
                <th>Date</th>
                <th>Source</th>
                <th>Scope</th>
                <th>Location</th>
                <th>Qty</th>
                <th>Emissions</th>
                <th>Status</th>
                <th>Flags</th>
              </tr>
            </thead>
            <tbody>
              {isLoading
                ? [...Array(8)].map((_, i) => <SkeletonRow key={i} cols={9} />)
                : records.length === 0
                  ? <tr><td colSpan={9}><EmptyState message="No records match your filters" icon="🔍" /></td></tr>
                  : records.map((r) => (
                      <tr
                        key={r.id}
                        onClick={() => setSelectedRecord(r)}
                        className={selectedIds.has(r.id) ? 'bg-ocean-50 border-ocean-200' : ''}
                      >
                        <td onClick={(e) => e.stopPropagation()}>
                          <input type="checkbox" checked={selectedIds.has(r.id)}
                            onChange={() => toggleSelect(r.id)} className="rounded border-slate-300" />
                        </td>
                        <td className="font-mono text-xs text-slate-500 font-medium">
                          {r.activity_date ? format(new Date(r.activity_date), 'MMM d') : '—'}
                        </td>
                        <td><SourceTypeBadge type={r.source_type} /></td>
                        <td><ScopeBadge scope={r.scope_category} /></td>
                        <td className="text-slate-700 font-medium max-w-[110px] truncate">{r.location || '—'}</td>
                        <td className="font-mono text-xs font-medium text-slate-700">
                          {r.normalized_quantity != null ? safeNumber(r.normalized_quantity).toFixed(1) : '—'}
                          <span className="text-slate-400 ml-1">{r.normalized_unit}</span>
                        </td>
                        <td><EmissionsValue value={r.calculated_emissions} /></td>
                        <td><StatusBadge status={r.status} /></td>
                        <td className="space-y-1">
                          {r.suspicious_flag && (
                            <SuspiciousIndicator flag reasons={Array.isArray(r.suspicious_reasons) ? r.suspicious_reasons : []} />
                          )}
                          {r.is_duplicate && (
                            <span className="badge bg-orange-50 text-orange-700 border-orange-200">🔄 Dup</span>
                          )}
                        </td>
                      </tr>
                    ))
              }
            </tbody>
          </table>
        </div>
        {pagination && pagination.total_pages > 1 && (
          <Pagination
            current={pagination.current_page}
            total={pagination.total_pages}
            count={pagination.count}
            onPrev={() => setPage((p) => Math.max(1, p - 1))}
            onNext={() => setPage((p) => p + 1)}
          />
        )}
      </div>

      {selectedRecord && <ReviewModal record={selectedRecord} onClose={() => setSelectedRecord(null)} />}
    </div>
  )
}
