import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { auditApi } from '@/services/api'
import { SkeletonRow, EmptyState, Pagination } from '@/components/ui/Badges'
import { format, formatDistanceToNow } from 'date-fns'
import { safeNumber } from '@/utils/format'

const ACTION_META: Record<string, { icon: string; color: string; bg: string; border: string }> = {
  file_uploaded:        { icon: '📤', color: 'text-ocean-700',  bg: 'bg-ocean-50',  border: 'border-ocean-200' },
  ingestion_started:    { icon: '⚙️', color: 'text-slate-600',  bg: 'bg-slate-50',  border: 'border-slate-200' },
  ingestion_completed:  { icon: '✅', color: 'text-teal-700',   bg: 'bg-teal-50',   border: 'border-teal-200'  },
  ingestion_failed:     { icon: '❌', color: 'text-red-700',    bg: 'bg-red-50',    border: 'border-red-200'   },
  record_flagged:       { icon: '🚩', color: 'text-amber-700',  bg: 'bg-amber-50',  border: 'border-amber-200' },
  record_approved:      { icon: '✅', color: 'text-teal-700',   bg: 'bg-teal-50',   border: 'border-teal-200'  },
  record_rejected:      { icon: '❌', color: 'text-red-700',    bg: 'bg-red-50',    border: 'border-red-200'   },
  record_locked:        { icon: '🔒', color: 'text-purple-700', bg: 'bg-purple-50', border: 'border-purple-200'},
  record_edited:        { icon: '✏️', color: 'text-ocean-700',  bg: 'bg-ocean-50',  border: 'border-ocean-200' },
  note_added:           { icon: '📝', color: 'text-slate-700',  bg: 'bg-slate-50',  border: 'border-slate-200' },
  bulk_approved:        { icon: '✅✅', color: 'text-teal-700',  bg: 'bg-teal-50',   border: 'border-teal-200'  },
  bulk_rejected:        { icon: '❌❌', color: 'text-red-700',   bg: 'bg-red-50',    border: 'border-red-200'   },
}

const defaultMeta = { icon: '📋', color: 'text-slate-600', bg: 'bg-slate-50', border: 'border-slate-200' }

export default function AuditHistoryPage() {
  const [page, setPage]         = useState(1)
  const [actionFilter, setActionFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['audit-logs', page, actionFilter],
    queryFn: () => auditApi.list({
      page,
      page_size: 30,
      ...(actionFilter ? { action: actionFilter } : {}),
    }),
  })

  const logs       = data?.data?.results || []
  const pagination = data?.data

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Audit History</h1>
        <p className="text-slate-500 text-sm mt-1">Immutable, tamper-proof record of all platform actions</p>
      </div>

      {/* Info banner */}
      <div className="alert-info">
        <span className="text-xl flex-shrink-0">🔒</span>
        <div className="text-sm">
          <strong>Immutable audit trail</strong> — all entries are append-only and cannot be modified or deleted.
          Timestamps are stored in UTC.
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4 flex gap-3">
        <select
          value={actionFilter}
          onChange={(e) => { setActionFilter(e.target.value); setPage(1) }}
          className="input-field w-60"
        >
          <option value="">All Action Types</option>
          {Object.keys(ACTION_META).map((a) => (
            <option key={a} value={a}>{ACTION_META[a].icon} {a.replace(/_/g, ' ')}</option>
          ))}
        </select>
        {pagination && (
          <div className="flex items-center text-sm text-slate-500 ml-2">
            <strong className="text-slate-700 mr-1">{safeNumber(pagination.count).toLocaleString()}</strong> total log entries
          </div>
        )}
      </div>

      {/* Audit table */}
      <div className="card overflow-hidden">
        <div className="tbl-wrap">
          <table className="tbl">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Action</th>
                <th>Actor</th>
                <th>Target</th>
                <th>Change</th>
                <th>Notes</th>
                <th>IP Address</th>
              </tr>
            </thead>
            <tbody>
              {isLoading
                ? [...Array(8)].map((_, i) => <SkeletonRow key={i} cols={7} />)
                : logs.length === 0
                  ? <tr><td colSpan={7}><EmptyState message="No audit logs yet" icon="📋" /></td></tr>
                  : logs.map((log: any) => {
                      const m = ACTION_META[log.action] || defaultMeta
                      return (
                        <tr key={log.id}>
                          <td className="whitespace-nowrap">
                            <div className="text-xs font-mono font-medium text-slate-700">
                              {format(new Date(log.timestamp), 'MMM d, HH:mm:ss')}
                            </div>
                            <div className="text-[10px] text-slate-400 mt-0.5">
                              {formatDistanceToNow(new Date(log.timestamp), { addSuffix: true })}
                            </div>
                          </td>
                          <td>
                            <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-semibold border ${m.bg} ${m.color} ${m.border}`}>
                              <span>{m.icon}</span>
                              <span className="capitalize">{log.action.replace(/_/g, ' ')}</span>
                            </span>
                          </td>
                          <td className="font-semibold text-slate-700 text-sm">{log.actor_name}</td>
                          <td>
                            <div className="text-xs font-semibold text-ocean-600 capitalize">{log.target_type?.replace(/_/g, ' ')}</div>
                            <div className="text-xs font-mono text-slate-400 mt-0.5 max-w-[100px] truncate">
                              {log.target_repr || log.target_id?.slice(0, 8)}
                            </div>
                          </td>
                          <td>
                            {log.before_state?.status && log.after_state?.status ? (
                              <div className="flex items-center gap-1.5 text-xs font-semibold">
                                <span className="px-1.5 py-0.5 bg-amber-50 text-amber-700 border border-amber-200 rounded-full">{log.before_state.status}</span>
                                <span className="text-slate-400">→</span>
                                <span className="px-1.5 py-0.5 bg-teal-50 text-teal-700 border border-teal-200 rounded-full">{log.after_state.status}</span>
                              </div>
                            ) : <span className="text-slate-400 text-xs">—</span>}
                          </td>
                          <td className="max-w-[180px]">
                            {log.notes
                              ? <span className="text-xs text-slate-600 line-clamp-2">{log.notes}</span>
                              : <span className="text-slate-300 text-xs">—</span>}
                          </td>
                          <td className="font-mono text-xs text-slate-400">{log.ip_address || '—'}</td>
                        </tr>
                      )
                    })
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
