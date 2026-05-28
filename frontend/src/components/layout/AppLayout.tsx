import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { authApi } from '@/services/api'

const navItems = [
  { to: '/dashboard', icon: '📊', label: 'Dashboard' },
  { to: '/upload',    icon: '📤', label: 'Upload Center' },
  { to: '/review',    icon: '🔍', label: 'Review Queue' },
  { to: '/flagged',   icon: '🚩', label: 'Flagged Records' },
  { to: '/audit',     icon: '📋', label: 'Audit History' },
  { to: '/sources',   icon: '🗂️', label: 'Source Files' },
]

const ROLE_COLORS: Record<string, string> = {
  admin:    'bg-ocean-100 text-ocean-700',
  analyst:  'bg-teal-100 text-teal-700',
  reviewer: 'bg-amber-100 text-amber-700',
  viewer:   'bg-slate-100 text-slate-600',
}

export default function AppLayout() {
  const { user, tokens, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    if (tokens?.refresh) { try { await authApi.logout(tokens.refresh) } catch {} }
    logout()
    navigate('/login')
  }

  const initials = `${user?.first_name?.[0] ?? ''}${user?.last_name?.[0] ?? ''}`

  return (
    <div className="flex h-screen overflow-hidden bg-beach">
      {/* ── Sidebar ── */}
      <aside className="w-64 flex-shrink-0 flex flex-col bg-sidebar-bg border-r border-ocean-100 shadow-sidebar">

        {/* Logo */}
        <div className="px-5 py-5 border-b border-ocean-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-ocean-gradient flex items-center justify-center text-xl shadow-btn flex-shrink-0">
              🌿
            </div>
            <div>
              <div className="font-bold text-slate-800 text-sm leading-tight">Breathe ESG</div>
              <div className="text-[11px] text-ocean-500 font-medium leading-tight">Sustainability Platform</div>
            </div>
          </div>
        </div>

        {/* Tenant chip */}
        {user?.tenant && (
          <div className="px-4 py-3 border-b border-ocean-100">
            <div className="bg-ocean-50 border border-ocean-100 rounded-xl px-3 py-2.5">
              <div className="text-[10px] text-ocean-500 font-semibold uppercase tracking-wider mb-0.5">Organization</div>
              <div className="text-sm font-bold text-slate-800 truncate">{user.tenant.name}</div>
              <div className="text-[11px] text-slate-500 capitalize">{user.tenant.plan} Plan · {user.tenant.reporting_year}</div>
            </div>
          </div>
        )}

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
          {navItems.map(({ to, icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => isActive ? 'nav-item-active' : 'nav-item'}
            >
              <span className="text-base leading-none">{icon}</span>
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* User footer */}
        <div className="p-4 border-t border-ocean-100 bg-sand-50/60">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-xl bg-ocean-gradient flex items-center justify-center text-xs font-bold text-white flex-shrink-0 shadow-btn">
              {initials}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold text-slate-800 truncate">{user?.full_name}</div>
              <span className={`text-[11px] font-semibold px-1.5 py-0.5 rounded-md capitalize ${ROLE_COLORS[user?.role ?? 'viewer']}`}>
                {user?.role}
              </span>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="btn-secondary w-full text-xs py-2 justify-center"
          >
            Sign Out
          </button>
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-14 flex-shrink-0 flex items-center justify-between px-6 bg-white/80 backdrop-blur-sm border-b border-ocean-100">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" />
            <span className="text-xs font-medium text-slate-500">Live · GHG Protocol 2023</span>
          </div>
          <div className="flex items-center gap-3 text-sm text-slate-500">
            <span className="text-ocean-600 font-semibold">{user?.tenant?.name}</span>
            <span>·</span>
            <span>FY {user?.tenant?.reporting_year ?? 2024}</span>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-6 animate-fade-in">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
