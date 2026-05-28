import { useQuery } from '@tanstack/react-query'
import { ingestionApi } from '@/services/api'
import { SkeletonRow, EmptyState } from '@/components/ui/Badges'
import { format } from 'date-fns'
import { safeNumber } from '@/utils/format'

function ProcessingBar({ processed, total }: { processed: unknown; total: unknown }) {
  const p = safeNumber(processed)
  const t = safeNumber(total)
  const pct = t > 0 ? Math.min((p / t) * 100, 100) : 0
  const color = pct >= 90 ? 'bg-teal-400' : pct >= 50 ? 'bg-amber-400' : 'bg-red-400'
  const textColor = pct >= 90 ? 'text-teal-700' : pct >= 50 ? 'text-amber-700' : 'text-red-700'
  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-slate-500">{p.toLocaleString()} / {t.toLocaleString()}</span>
        <span className={`font-bold ${textColor}`}>{pct.toFixed(0)}%</span>
      </div>
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-700`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

const STATUS_CFG: Record<string, { badge: string; dot: string; label: string }> = {
  pending:    { badge: 'bg-amber-50 text-amber-700 border-amber-200',  dot: 'bg-amber-400 animate-pulse', label: 'Pending' },
  processing: { badge: 'bg-ocean-50 text-ocean-700 border-ocean-200',  dot: 'bg-ocean-400 animate-pulse', label: 'Processing' },
  processed:  { badge: 'bg-teal-50 text-teal-700 border-teal-200',    dot: 'bg-teal-500',                label: 'Processed' },
  failed:     { badge: 'bg-red-50 text-red-700 border-red-200',       dot: 'bg-red-500',                 label: 'Failed' },
}

const SOURCE_CFG: Record<string, { label: string; icon: string; color: string }> = {
  sap_fuel:            { label: 'SAP Fuel',   icon: '⛽', color: 'text-amber-700' },
  utility_electricity: { label: 'Utility',    icon: '⚡', color: 'text-ocean-700' },
  corporate_travel:    { label: 'Travel',     icon: '✈️', color: 'text-teal-700'  },
}

export default function SourceManagementPage() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['source-files'],
    queryFn:  () => ingestionApi.list(),
    refetchInterval: 8000,
  })

  const files: any[] = data?.data?.data || []

  const totals = files.reduce(
    (acc, f) => ({
      total_rows:     acc.total_rows     + (f.total_rows     || 0),
      processed_rows: acc.processed_rows + (f.processed_rows || 0),
      flagged_rows:   acc.flagged_rows   + (f.flagged_rows   || 0),
      failed_rows:    acc.failed_rows    + (f.failed_rows    || 0),
    }),
    { total_rows: 0, processed_rows: 0, flagged_rows: 0, failed_rows: 0 }
  )

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Source File Management</h1>
          <p className="text-slate-500 text-sm mt-1">Track all ingested data sources and their processing status</p>
        </div>
        <button onClick={() => refetch()} className="btn-secondary">
          🔄 Refresh
        </button>
      </div>

      {/* Aggregate stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Files',     value: safeNumber(files.length).toLocaleString(),              icon: '🗂️', color: 'ocean' },
          { label: 'Total Rows',      value: safeNumber(totals.total_rows).toLocaleString(),     icon: '📊', color: 'teal'  },
          { label: 'Flagged Rows',    value: safeNumber(totals.flagged_rows).toLocaleString(),   icon: '🚩', color: 'amber' },
          { label: 'Failed Rows',     value: safeNumber(totals.failed_rows).toLocaleString(),    icon: '❌', color: 'red'   },
        ].map(({ label, value, icon, color }) => {
          const colorMap: Record<string, string> = {
            ocean: 'from-ocean-50 to-white border-ocean-200',
            teal:  'from-teal-50 to-white border-teal-200',
            amber: 'from-amber-50 to-white border-amber-200',
            red:   'from-red-50 to-white border-red-200',
          }
          const iconMap: Record<string, string> = {
            ocean: 'bg-ocean-100 text-ocean-600',
            teal:  'bg-teal-100 text-teal-600',
            amber: 'bg-amber-100 text-amber-600',
            red:   'bg-red-100 text-red-600',
          }
          return (
            <div key={label} className={`card p-5 bg-gradient-to-br ${colorMap[color]} border`}>
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-xl mb-3 ${iconMap[color]}`}>{icon}</div>
              <div className="text-2xl font-bold text-slate-800">{value}</div>
              <div className="text-sm font-medium text-slate-500 mt-0.5">{label}</div>
            </div>
          )
        })}
      </div>

      {/* File table */}
      <div className="card overflow-hidden">
        <div className="px-5 py-4 border-b border-ocean-100 flex items-center justify-between">
          <div className="font-bold text-slate-800">All Source Files</div>
          <div className="flex items-center gap-1.5 text-xs text-teal-600 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
            Auto-refreshing every 8s
          </div>
        </div>
        <div className="tbl-wrap">
          <table className="tbl">
            <thead>
              <tr>
                <th>Filename</th>
                <th>Source Type</th>
                <th>Status</th>
                <th>Processing Progress</th>
                <th>Flagged</th>
                <th>Failed</th>
                <th>Uploaded By</th>
                <th>Upload Date</th>
              </tr>
            </thead>
            <tbody>
              {isLoading
                ? [...Array(4)].map((_, i) => <SkeletonRow key={i} cols={8} />)
                : files.length === 0
                  ? <tr><td colSpan={8}><EmptyState message="No source files uploaded yet" icon="📤" /></td></tr>
                  : files.map((sf) => {
                      const s = STATUS_CFG[sf.status] || STATUS_CFG.pending
                      const src = SOURCE_CFG[sf.source_type] || { label: sf.source_type, icon: '📄', color: 'text-slate-600' }
                      return (
                        <tr key={sf.id}>
                          <td>
                            <div className="font-semibold text-slate-800 max-w-[200px] truncate text-sm">{sf.original_filename}</div>
                            <div className="text-[10px] font-mono text-slate-400 mt-0.5">{sf.id?.slice(0, 12)}…</div>
                          </td>
                          <td>
                            <span className={`font-semibold text-sm ${src.color}`}>{src.icon} {src.label}</span>
                          </td>
                          <td>
                            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${s.badge}`}>
                              <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
                              {s.label}
                            </span>
                          </td>
                          <td className="min-w-[160px]">
                            <ProcessingBar processed={sf.processed_rows} total={sf.total_rows} />
                          </td>
                          <td>
                            <span className={`text-sm font-bold ${sf.flagged_rows > 0 ? 'text-red-600' : 'text-slate-400'}`}>
                              {sf.flagged_rows || 0}
                            </span>
                          </td>
                          <td>
                            <span className={`text-sm font-bold ${sf.failed_rows > 0 ? 'text-amber-600' : 'text-slate-400'}`}>
                              {sf.failed_rows || 0}
                            </span>
                          </td>
                          <td className="text-sm font-medium text-slate-600">{sf.uploaded_by_name || '—'}</td>
                          <td className="text-xs text-slate-500 whitespace-nowrap font-mono">
                            {sf.ingestion_timestamp ? format(new Date(sf.ingestion_timestamp), 'MMM d, HH:mm') : '—'}
                          </td>
                        </tr>
                      )
                    })
              }
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
