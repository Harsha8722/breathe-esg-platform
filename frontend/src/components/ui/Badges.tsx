import type { RecordStatus, ScopeCategory, SourceType } from '@/types'
import { safeNumber } from '@/utils/format'

/* ─── Status Badge ─── */
export function StatusBadge({ status }: { status: RecordStatus }) {
  const cfg: Record<RecordStatus, { cls: string; dot: string; label: string }> = {
    pending:  { cls: 'badge-pending',  dot: 'bg-amber-400',                 label: 'Pending'  },
    flagged:  { cls: 'badge-flagged',  dot: 'bg-red-500 animate-pulse',      label: 'Flagged'  },
    approved: { cls: 'badge-approved', dot: 'bg-teal-500',                  label: 'Approved' },
    rejected: { cls: 'badge-rejected', dot: 'bg-slate-400',                 label: 'Rejected' },
    locked:   { cls: 'badge-locked',   dot: 'bg-purple-500',                label: 'Locked'   },
  }
  const c = cfg[status] ?? cfg.pending
  return (
    <span className={c.cls}>
      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${c.dot}`} />
      {c.label}
    </span>
  )
}

/* ─── Scope Badge ─── */
export function ScopeBadge({ scope }: { scope: ScopeCategory }) {
  const cfg = {
    scope_1: { label: 'Scope 1', cls: 'bg-sunset-50 text-sunset-700 border-sunset-200' },
    scope_2: { label: 'Scope 2', cls: 'bg-ocean-50 text-ocean-700 border-ocean-200' },
    scope_3: { label: 'Scope 3', cls: 'bg-purple-50 text-purple-700 border-purple-200' },
  }
  const c = cfg[scope] ?? cfg.scope_1
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border ${c.cls}`}>
      {c.label}
    </span>
  )
}

/* ─── Source Type Badge ─── */
export function SourceTypeBadge({ type }: { type: SourceType }) {
  const cfg: Record<SourceType, { label: string; icon: string; cls: string }> = {
    sap_fuel:            { label: 'SAP Fuel',   icon: '⛽', cls: 'bg-amber-50 text-amber-700 border-amber-200' },
    utility_electricity: { label: 'Utility',    icon: '⚡', cls: 'bg-ocean-50 text-ocean-700 border-ocean-200' },
    corporate_travel:    { label: 'Travel',     icon: '✈️', cls: 'bg-teal-50 text-teal-700 border-teal-200'   },
  }
  const c = cfg[type] ?? { label: type, icon: '📄', cls: 'bg-slate-50 text-slate-600 border-slate-200' }
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold border ${c.cls}`}>
      <span>{c.icon}</span>{c.label}
    </span>
  )
}

/* ─── Suspicious Indicator ─── */
export function SuspiciousIndicator({ flag, reasons }: { flag: boolean; reasons?: string[] }) {
  if (!flag) return null
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-50 border border-red-200 rounded-full text-xs font-semibold text-red-700"
      title={reasons?.join('; ')}
    >
      ⚠️ Suspicious
    </span>
  )
}

/* ─── Emissions Value ─── */
export function EmissionsValue({ value, unit = 'kgCO₂e' }: { value: unknown; unit?: string }) {
  // DRF DecimalField returns strings — convert safely before calling .toFixed()
  if (value === null || value === undefined) return <span className="text-slate-400 font-mono text-sm">—</span>
  const n = Number(value)
  if (!Number.isFinite(n)) return <span className="text-slate-400 font-mono text-sm">—</span>
  const formatted = n >= 1000 ? `${(n / 1000).toFixed(2)} tCO₂e` : `${n.toFixed(2)} ${unit}`
  return <span className="font-mono text-sm text-slate-800 font-medium">{formatted}</span>
}

/* ─── Skeleton Row ─── */
export function SkeletonRow({ cols = 8 }: { cols?: number }) {
  return (
    <tr>
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="py-3 px-4">
          <div className="skeleton h-4 w-full max-w-[100px]" />
        </td>
      ))}
    </tr>
  )
}

/* ─── Empty State ─── */
export function EmptyState({ message = 'No records found', icon = '🌊' }: { message?: string; icon?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="text-5xl mb-4 animate-wave">{icon}</div>
      <p className="text-slate-500 font-medium">{message}</p>
      <p className="text-slate-400 text-sm mt-1">Try adjusting your filters</p>
    </div>
  )
}

/* ─── Stat Card ─── */
export function StatCard({
  label, value, sub, icon, trend, color = 'ocean',
}: {
  label: string; value: string | number; sub?: string; icon: string; trend?: number; color?: string
}) {
  const colorMap: Record<string, { bg: string; icon: string; bar: string }> = {
    ocean:  { bg: 'from-ocean-50 to-white border-ocean-200',    icon: 'bg-ocean-100 text-ocean-600',  bar: 'bg-ocean-400' },
    teal:   { bg: 'from-teal-50 to-white border-teal-200',      icon: 'bg-teal-100 text-teal-600',    bar: 'bg-teal-400' },
    amber:  { bg: 'from-amber-50 to-white border-amber-200',    icon: 'bg-amber-100 text-amber-600',  bar: 'bg-amber-400' },
    red:    { bg: 'from-red-50 to-white border-red-200',        icon: 'bg-red-100 text-red-600',      bar: 'bg-red-400' },
    purple: { bg: 'from-purple-50 to-white border-purple-200',  icon: 'bg-purple-100 text-purple-600', bar: 'bg-purple-400' },
    slate:  { bg: 'from-slate-50 to-white border-slate-200',    icon: 'bg-slate-100 text-slate-500',  bar: 'bg-slate-400' },
  }
  const c = colorMap[color] ?? colorMap.ocean
  return (
    <div className={`card p-5 bg-gradient-to-br ${c.bg} border transition-all duration-300 hover:shadow-card-hover hover:-translate-y-0.5`}>
      <div className="flex items-start justify-between mb-3">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-xl ${c.icon}`}>
          {icon}
        </div>
        {trend !== undefined && (
          <span className={`text-xs font-bold px-2 py-1 rounded-full ${trend >= 0 ? 'bg-teal-100 text-teal-700' : 'bg-red-100 text-red-700'}`}>
            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
          </span>
        )}
      </div>
      <div className="text-2xl font-bold text-slate-800 tracking-tight">{value}</div>
      <div className="text-sm font-medium text-slate-600 mt-0.5">{label}</div>
      {sub && <div className="text-xs text-slate-400 mt-1">{sub}</div>}
    </div>
  )
}

/* ─── Pagination ─── */
export function Pagination({
  current, total, count, onPrev, onNext
}: {
  current: number; total: number; count: number; onPrev: () => void; onNext: () => void
}) {
  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-ocean-100">
      <span className="text-sm text-slate-500">
        Page <strong className="text-slate-700">{current}</strong> of <strong className="text-slate-700">{total}</strong>
        <span className="text-slate-400 ml-2">({safeNumber(count).toLocaleString()} records)</span>
      </span>
      <div className="flex gap-2">
        <button onClick={onPrev} disabled={current <= 1} className="btn-secondary text-xs py-1.5 px-3 disabled:opacity-40">← Prev</button>
        <button onClick={onNext} disabled={current >= total} className="btn-secondary text-xs py-1.5 px-3 disabled:opacity-40">Next →</button>
      </div>
    </div>
  )
}
