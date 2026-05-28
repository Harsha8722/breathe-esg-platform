import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { authApi } from '@/services/api'
import { useAuthStore } from '@/store/authStore'

export default function LoginPage() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPwd, setShowPwd] = useState(false)
  const [remember, setRemember] = useState(false)
  const [error, setError] = useState('')

  const loginMutation = useMutation({
    mutationFn: () => authApi.login(email, password),
    onSuccess: (res) => { setAuth(res.data.data); navigate('/dashboard') },
    onError: (err: any) => {
      setError(err.response?.data?.error?.message || 'Invalid credentials. Please try again.')
    },
  })

  const handleSubmit = (e: React.FormEvent) => { e.preventDefault(); setError(''); loginMutation.mutate() }

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden" style={{
      background: 'linear-gradient(160deg, #e0f2fe 0%, #bae6fd 25%, #a5f3fc 55%, #99f6e4 80%, #ccfbf1 100%)'
    }}>
      {/* Decorative ocean waves */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <svg className="absolute bottom-0 left-0 right-0 w-full" viewBox="0 0 1440 200" preserveAspectRatio="none">
          <path d="M0,100 C360,180 720,20 1080,100 C1260,140 1380,80 1440,100 L1440,200 L0,200 Z"
            fill="rgba(255,255,255,0.35)" />
          <path d="M0,130 C480,60 960,180 1440,130 L1440,200 L0,200 Z"
            fill="rgba(255,255,255,0.5)" />
        </svg>
        {/* Floating bubbles */}
        {[
          { size: 120, left: '8%', top: '15%', delay: '0s' },
          { size: 80,  left: '85%', top: '10%', delay: '1.5s' },
          { size: 60,  left: '70%', top: '60%', delay: '0.8s' },
          { size: 40,  left: '20%', top: '70%', delay: '2s' },
        ].map((b, i) => (
          <div key={i} className="absolute rounded-full opacity-20"
            style={{
              width: b.size, height: b.size,
              left: b.left, top: b.top,
              background: 'linear-gradient(135deg, #0ea5e9, #06b6d4)',
              animationName: 'float',
              animationDuration: '6s',
              animationDelay: b.delay,
              animationIterationCount: 'infinite',
              animationTimingFunction: 'ease-in-out',
            }}
          />
        ))}
      </div>

      {/* Login card */}
      <div className="relative w-full max-w-md mx-4 animate-slide-up">
        <div className="bg-white rounded-3xl shadow-modal overflow-hidden">

          {/* Ocean header strip */}
          <div className="h-2 bg-ocean-gradient" />

          <div className="p-8">
            {/* Logo */}
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-ocean-gradient shadow-btn mb-4">
                <span className="text-3xl">🌿</span>
              </div>
              <h1 className="text-2xl font-bold text-slate-800">Breathe ESG Platform</h1>
              <p className="text-slate-500 text-sm mt-1">Enterprise Sustainability Analytics</p>
            </div>

            {/* Error */}
            {error && (
              <div className="alert-error text-sm mb-5">
                <span className="text-lg flex-shrink-0">⚠️</span>
                <span className="font-medium">{error}</span>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="input-label" htmlFor="email">Email address</label>
                <input
                  id="email" type="email" value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-field" placeholder="analyst@company.com" required
                />
              </div>

              <div>
                <label className="input-label" htmlFor="password">Password</label>
                <div className="relative">
                  <input
                    id="password" type={showPwd ? 'text' : 'password'} value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input-field pr-12" placeholder="••••••••" required
                  />
                  <button type="button" onClick={() => setShowPwd(!showPwd)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-ocean-600 transition-colors text-sm font-medium">
                    {showPwd ? 'Hide' : 'Show'}
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input id="remember" type="checkbox" checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                  className="w-4 h-4 rounded border-slate-300 text-ocean-600 focus:ring-ocean-300" />
                <label htmlFor="remember" className="text-sm text-slate-600 cursor-pointer">Remember me</label>
              </div>

              <button type="submit" disabled={loginMutation.isPending} className="btn-primary w-full py-3 mt-2 text-base">
                {loginMutation.isPending
                  ? <><span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" /> Signing in...</>
                  : '🌊 Sign In'}
              </button>
            </form>


          </div>
        </div>

        {/* Create account link */}
        <p className="text-center text-sm text-white/90 mt-4 drop-shadow font-medium">
          New to Breathe ESG?{' '}
          <Link to="/register"
            className="underline underline-offset-2 hover:text-white transition-colors font-bold">
            Create an account →
          </Link>
        </p>

        <p className="text-center text-xs text-white/60 mt-2 drop-shadow">
          GHG Protocol Compliant · SOC 2 Ready · Enterprise Grade
        </p>
      </div>
    </div>
  )
}
