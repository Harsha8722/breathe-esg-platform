import { useQuery } from '@tanstack/react-query'
import { emissionsApi, analyticsApi } from '@/services/api'
import { StatCard } from '@/components/ui/Badges'
import { safeNumber } from '@/utils/format'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, BarChart, Bar,
} from 'recharts'

const SCOPE_COLORS  = ['#f97316', '#0ea5e9', '#a855f7']
const SOURCE_COLORS = ['#f59e0b', '#0ea5e9', '#14b8a6']

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <div className="h-5 w-1 rounded-full bg-ocean-gradient" />
      <h2 className="text-sm font-bold text-slate-700 uppercase tracking-wider">{children}</h2>
    </div>
  )
}

export default function DashboardPage() {
  const { data: summaryRes, isLoading: summaryLoading } = useQuery({
    queryKey: ['emissions-summary'], queryFn: () => emissionsApi.summary(),
  })
  const { data: trendRes }     = useQuery({ queryKey: ['scope-trend'],       queryFn: () => analyticsApi.scopeTrend('2024') })
  const { data: breakdownRes } = useQuery({ queryKey: ['source-breakdown'],  queryFn: () => analyticsApi.sourceBreakdown() })

  const summary       = summaryRes?.data?.data
  const trendRaw      = trendRes?.data?.data || []
  const breakdownData = breakdownRes?.data?.data || []

  // Pivot trend data for Recharts
  const chartData = trendRaw.reduce((acc: any[], row: any) => {
    const m = acc.find((d) => d.month === row.month)
    if (m) m[row.scope_category] = row.total_emissions
    else acc.push({ month: row.month, [row.scope_category]: row.total_emissions })
    return acc
  }, [])

  const pieData = breakdownData.map((d: any, i: number) => ({
    name: d.source_type === 'sap_fuel' ? 'SAP Fuel' : d.source_type === 'utility_electricity' ? 'Electricity' : 'Travel',
    value: Math.round(d.total_emissions_kgco2e || 0),
    fill: SOURCE_COLORS[i % SOURCE_COLORS.length],
  }))

  const total = safeNumber(summary?.total_emissions_kgco2e)

  return (
    <div className="space-y-7 animate-fade-in">
      {/* Page header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 tracking-tight">ESG Dashboard</h1>
          <p className="text-slate-500 text-sm mt-1">Real-time overview of your sustainability data pipeline</p>
        </div>
        <div className="flex items-center gap-2 bg-teal-50 border border-teal-200 rounded-xl px-4 py-2.5">
          <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" />
          <span className="text-sm font-semibold text-teal-700">Live · FY 2024</span>
        </div>
      </div>

      {/* KPI row */}
      {summaryLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-32 rounded-2xl" />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Total Records" value={summary?.total_records?.toLocaleString() ?? '0'}
            sub="All ingested rows" icon="📊" color="ocean" />
          <StatCard label="Pending Review" value={summary?.pending?.toLocaleString() ?? '0'}
            sub="Awaiting analyst" icon="⏳" color="amber" />
          <StatCard label="Flagged" value={summary?.flagged?.toLocaleString() ?? '0'}
            sub="Needs attention" icon="🚩" color="red" />
          <StatCard label="Approved" value={summary?.approved?.toLocaleString() ?? '0'}
            sub="Verified records" icon="✅" color="teal" />
        </div>
      )}

      {/* Emissions summary + pipeline + pie */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Total emissions */}
        <div className="card p-6">
          <SectionTitle>Verified Emissions</SectionTitle>
          <div className="text-4xl font-bold text-ocean-gradient mb-1">
            {total >= 1000 ? `${(total / 1000).toFixed(1)}t` : `${total.toFixed(0)} kg`}
          </div>
          <div className="text-sm font-medium text-slate-500 mb-5">CO₂ equivalent (approved + locked)</div>
          <div className="space-y-4">
            {[
              { label: 'Scope 1 — Direct', value: safeNumber(summary?.total_scope1_kgco2e), color: 'bg-sunset-500', text: 'text-sunset-600' },
              { label: 'Scope 2 — Energy', value: safeNumber(summary?.total_scope2_kgco2e), color: 'bg-ocean-500',  text: 'text-ocean-600' },
              { label: 'Scope 3 — Value Chain', value: safeNumber(summary?.total_scope3_kgco2e), color: 'bg-purple-500', text: 'text-purple-600' },
            ].map(({ label, value, color, text }) => {
              const pct = total > 0 ? Math.min((value / total) * 100, 100) : 0
              return (
                <div key={label}>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="font-medium text-slate-600">{label}</span>
                    <span className={`font-bold font-mono ${text}`}>
                      {value >= 1000 ? `${(value / 1000).toFixed(1)}t` : `${safeNumber(value).toFixed(0)} kg`}
                    </span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className={`h-full ${color} rounded-full transition-all duration-700`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Source breakdown pie */}
        <div className="card p-6">
          <SectionTitle>Emissions by Source</SectionTitle>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={pieData} dataKey="value" cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={4}>
                  {pieData.map((e: any, i: number) => <Cell key={i} fill={e.fill} />)}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#fff', border: '1px solid #bae6fd', borderRadius: 12, fontSize: 12, color: '#334155' }}
                  formatter={(v: number) => [`${v.toLocaleString()} kgCO₂e`]}
                />
                <Legend iconSize={10} wrapperStyle={{ fontSize: 12, color: '#475569' }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-48 text-slate-400 text-sm">No approved data yet</div>
          )}
        </div>

        {/* Review pipeline */}
        <div className="card p-6">
          <SectionTitle>Review Pipeline</SectionTitle>
          <div className="space-y-3.5">
            {[
              { label: 'Pending',  count: summary?.pending  || 0, color: 'bg-amber-400',  text: 'text-amber-700',  bg: 'bg-amber-50' },
              { label: 'Flagged',  count: summary?.flagged  || 0, color: 'bg-red-500',    text: 'text-red-700',    bg: 'bg-red-50' },
              { label: 'Approved', count: summary?.approved || 0, color: 'bg-teal-500',   text: 'text-teal-700',   bg: 'bg-teal-50' },
              { label: 'Rejected', count: summary?.rejected || 0, color: 'bg-slate-400',  text: 'text-slate-600',  bg: 'bg-slate-50' },
              { label: 'Locked',   count: summary?.locked   || 0, color: 'bg-purple-500', text: 'text-purple-700', bg: 'bg-purple-50' },
            ].map(({ label, count, color, text, bg }) => {
              const pct = ((summary?.total_records || 1) > 0) ? (count / (summary?.total_records || 1)) * 100 : 0
              return (
                <div key={label} className="flex items-center gap-3">
                  <div className={`text-xs font-semibold ${text} ${bg} px-2 py-0.5 rounded-full w-20 text-center flex-shrink-0`}>{label}</div>
                  <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className={`h-full ${color} rounded-full transition-all duration-700`} style={{ width: `${pct}%` }} />
                  </div>
                  <div className={`text-sm font-bold ${text} w-10 text-right`}>{count}</div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Trend chart */}
      {chartData.length > 0 && (
        <div className="card p-6">
          <SectionTitle>Monthly Emissions Trend (2024)</SectionTitle>
          <ResponsiveContainer width="100%" height={230}>
            <AreaChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
              <defs>
                {['scope_1', 'scope_2', 'scope_3'].map((s, i) => (
                  <linearGradient key={s} id={`ag-${s}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor={SCOPE_COLORS[i]} stopOpacity={0.25} />
                    <stop offset="95%" stopColor={SCOPE_COLORS[i]} stopOpacity={0} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#64748b' }} />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
              <Tooltip
                contentStyle={{ background: '#fff', border: '1px solid #bae6fd', borderRadius: 12, fontSize: 12, color: '#334155' }}
                labelStyle={{ color: '#0369a1', fontWeight: 600 }}
              />
              {['scope_1', 'scope_2', 'scope_3'].map((s, i) => (
                <Area key={s} type="monotone" dataKey={s} stroke={SCOPE_COLORS[i]}
                  fill={`url(#ag-${s})`} strokeWidth={2.5} />
              ))}
            </AreaChart>
          </ResponsiveContainer>
          <div className="flex items-center gap-5 mt-3 justify-center">
            {['Scope 1 (Direct)', 'Scope 2 (Energy)', 'Scope 3 (Value Chain)'].map((l, i) => (
              <div key={l} className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-full" style={{ background: SCOPE_COLORS[i] }} />
                <span className="text-xs font-medium text-slate-600">{l}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
