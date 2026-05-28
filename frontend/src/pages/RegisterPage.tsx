import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { authApi } from '@/services/api'
import { useAuthStore } from '@/store/authStore'

/* ── password strength ─────────────────────── */
function getPasswordStrength(pw: string) {
  let score = 0
  if (pw.length >= 8)  score++
  if (pw.length >= 12) score++
  if (/[A-Z]/.test(pw)) score++
  if (/[0-9]/.test(pw)) score++
  if (/[^A-Za-z0-9]/.test(pw)) score++
  if (score <= 1) return { label: 'Weak',   color: '#ef4444', width: '20%' }
  if (score <= 2) return { label: 'Fair',   color: '#f97316', width: '40%' }
  if (score <= 3) return { label: 'Good',   color: '#eab308', width: '60%' }
  if (score <= 4) return { label: 'Strong', color: '#22c55e', width: '80%' }
  return            { label: 'Excellent', color: '#0ea5e9', width: '100%' }
}

/* ── floating bubble background (reused from LoginPage) ─── */
const BUBBLES = [
  { size: 140, left: '6%',  top: '12%', delay: '0s'   },
  { size: 90,  left: '88%', top: '8%',  delay: '1.2s' },
  { size: 65,  left: '75%', top: '58%', delay: '0.6s' },
  { size: 45,  left: '15%', top: '72%', delay: '2.1s' },
  { size: 55,  left: '50%', top: '85%', delay: '1.7s' },
]

const ROLES = [
  { value: 'analyst',  label: 'Analyst',  desc: 'Upload & process ESG data',        icon: '📊' },
  { value: 'reviewer', label: 'Reviewer', desc: 'Approve & review emissions records', icon: '🔍' },
  { value: 'viewer',   label: 'Viewer',   desc: 'Read-only access to dashboards',    icon: '👁️' },
]

/* ── step indicator ──────────────────────── */
function StepDot({ active, done, n }: { active: boolean; done: boolean; n: number }) {
  return (
    <div className="flex items-center gap-2">
      <div
        style={{
          width: 32, height: 32, borderRadius: '50%',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 700, fontSize: 13,
          background: done ? 'linear-gradient(135deg,#0ea5e9,#06b6d4)'
                    : active ? 'linear-gradient(135deg,#0ea5e9,#06b6d4)'
                    : '#e2e8f0',
          color: done || active ? '#fff' : '#94a3b8',
          boxShadow: active || done ? '0 2px 8px rgba(14,165,233,0.35)' : 'none',
          transition: 'all 0.3s ease',
          flexShrink: 0,
        }}
      >
        {done ? '✓' : n}
      </div>
    </div>
  )
}

export default function RegisterPage() {
  const navigate  = useNavigate()
  const setAuth   = useAuthStore((s) => s.setAuth)

  /* form state */
  const [step, setStep]         = useState(1)   // 1 = personal, 2 = role, 3 = password
  const [firstName, setFirstName] = useState('')
  const [lastName,  setLastName]  = useState('')
  const [email,     setEmail]     = useState('')
  const [role,      setRole]      = useState('analyst')
  const [password,  setPassword]  = useState('')
  const [confirm,   setConfirm]   = useState('')
  const [showPwd,   setShowPwd]   = useState(false)
  const [showConf,  setShowConf]  = useState(false)
  const [error,     setError]     = useState('')
  const [success,   setSuccess]   = useState(false)

  const strength = getPasswordStrength(password)
  const pwMatch  = confirm.length > 0 && password === confirm

  /* validation per step */
  const step1Valid = firstName.trim().length >= 2 && lastName.trim().length >= 2 && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
  const step2Valid = !!role
  const step3Valid = password.length >= 8 && password === confirm

  const registerMutation = useMutation({
    mutationFn: () =>
      authApi.register(firstName.trim(), lastName.trim(), email.trim(), password, confirm, role),
    onSuccess: (res: any) => {
      setSuccess(true)
      // Auto-login after registration
      setTimeout(() => {
        setAuth(res.data.data)
        navigate('/dashboard')
      }, 1800)
    },
    onError: (err: any) => {
      const data = err.response?.data
      if (data?.email)    setError(`Email: ${data.email[0]}`)
      else if (data?.password) setError(`Password: ${data.password[0]}`)
      else if (data?.detail)   setError(data.detail)
      else setError('Registration failed. Please try again.')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (step < 3) { setStep(s => s + 1); return }
    registerMutation.mutate()
  }

  /* ── Success screen ───────────────────────── */
  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center"
        style={{ background: 'linear-gradient(160deg,#e0f2fe 0%,#bae6fd 25%,#a5f3fc 55%,#99f6e4 80%,#ccfbf1 100%)' }}>
        <div className="bg-white rounded-3xl shadow-2xl p-10 text-center max-w-sm mx-4 animate-slide-up">
          <div className="w-20 h-20 rounded-full mx-auto mb-5 flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg,#0ea5e9,#14b8a6)', boxShadow: '0 8px 24px rgba(14,165,233,0.4)' }}>
            <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-slate-800 mb-2">Welcome aboard!</h2>
          <p className="text-slate-500 text-sm mb-1">Account created successfully.</p>
          <p className="text-slate-400 text-xs">Redirecting to your dashboard…</p>
          <div className="mt-5 h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full rounded-full animate-pulse-soft"
              style={{ width: '100%', background: 'linear-gradient(90deg,#0ea5e9,#14b8a6)' }} />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden py-8"
      style={{ background: 'linear-gradient(160deg,#e0f2fe 0%,#bae6fd 25%,#a5f3fc 55%,#99f6e4 80%,#ccfbf1 100%)' }}>

      {/* Decorative background */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <svg className="absolute bottom-0 left-0 right-0 w-full" viewBox="0 0 1440 200" preserveAspectRatio="none">
          <path d="M0,100 C360,180 720,20 1080,100 C1260,140 1380,80 1440,100 L1440,200 L0,200 Z"
            fill="rgba(255,255,255,0.3)" />
          <path d="M0,130 C480,60 960,180 1440,130 L1440,200 L0,200 Z"
            fill="rgba(255,255,255,0.45)" />
        </svg>
        {BUBBLES.map((b, i) => (
          <div key={i} className="absolute rounded-full opacity-20"
            style={{
              width: b.size, height: b.size, left: b.left, top: b.top,
              background: 'linear-gradient(135deg,#0ea5e9,#06b6d4)',
              animationName: 'float', animationDuration: '6s',
              animationDelay: b.delay, animationIterationCount: 'infinite',
              animationTimingFunction: 'ease-in-out',
            }} />
        ))}
      </div>

      {/* Card */}
      <div className="relative w-full max-w-md mx-4 animate-slide-up">
        <div className="bg-white rounded-3xl shadow-2xl overflow-hidden">

          {/* Gradient top bar */}
          <div className="h-2" style={{ background: 'linear-gradient(90deg,#0ea5e9,#06b6d4,#14b8a6)' }} />

          <div className="p-8">
            {/* Logo + title */}
            <div className="text-center mb-6">
              <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-3"
                style={{ background: 'linear-gradient(135deg,#0ea5e9,#06b6d4)', boxShadow: '0 4px 14px rgba(14,165,233,0.4)' }}>
                <span style={{ fontSize: 26 }}>🌿</span>
              </div>
              <h1 className="text-2xl font-bold text-slate-800">Create your account</h1>
              <p className="text-slate-500 text-sm mt-1">Join Breathe ESG Platform</p>
            </div>

            {/* Step indicator */}
            <div className="flex items-center justify-center gap-0 mb-7">
              {[1, 2, 3].map((n, idx) => (
                <div key={n} className="flex items-center">
                  <StepDot n={n} active={step === n} done={step > n} />
                  {idx < 2 && (
                    <div style={{
                      width: 48, height: 2, margin: '0 4px',
                      background: step > n ? 'linear-gradient(90deg,#0ea5e9,#06b6d4)' : '#e2e8f0',
                      transition: 'background 0.4s ease',
                    }} />
                  )}
                </div>
              ))}
            </div>
            <div className="flex justify-between text-[11px] font-semibold text-slate-400 mb-6 px-1">
              <span className={step >= 1 ? 'text-ocean-600' : ''}>Personal Info</span>
              <span className={step >= 2 ? 'text-ocean-600' : ''}>Your Role</span>
              <span className={step >= 3 ? 'text-ocean-600' : ''}>Set Password</span>
            </div>

            {/* Error banner */}
            {error && (
              <div className="alert-error text-sm mb-5">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="flex-shrink-0 mt-0.5">
                  <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <span className="font-medium">{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">

              {/* ── STEP 1: Personal Info ─── */}
              {step === 1 && (
                <div className="space-y-4 animate-fade-in">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="input-label" htmlFor="firstName">First name</label>
                      <input
                        id="firstName" type="text" value={firstName} autoFocus
                        onChange={e => setFirstName(e.target.value)}
                        className="input-field" placeholder="Alex" required minLength={2}
                      />
                    </div>
                    <div>
                      <label className="input-label" htmlFor="lastName">Last name</label>
                      <input
                        id="lastName" type="text" value={lastName}
                        onChange={e => setLastName(e.target.value)}
                        className="input-field" placeholder="Chen" required minLength={2}
                      />
                    </div>
                  </div>

                  <div>
                    <label className="input-label" htmlFor="reg-email">Work email</label>
                    <div className="relative">
                      <input
                        id="reg-email" type="email" value={email}
                        onChange={e => setEmail(e.target.value)}
                        className="input-field pl-10" placeholder="you@company.com" required
                      />
                      <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                        <polyline points="22,6 12,13 2,6" />
                      </svg>
                    </div>
                  </div>

                  <button type="submit" disabled={!step1Valid}
                    className="btn-primary w-full py-3 mt-1 text-base">
                    Continue →
                  </button>
                </div>
              )}

              {/* ── STEP 2: Role Selection ─── */}
              {step === 2 && (
                <div className="space-y-3 animate-fade-in">
                  <p className="text-sm text-slate-500 -mt-1 mb-4">
                    Choose your role. Admins can assign roles after you join.
                  </p>
                  {ROLES.map(r => (
                    <button
                      key={r.value} type="button"
                      onClick={() => setRole(r.value)}
                      className="w-full flex items-center gap-4 p-4 rounded-2xl border-2 text-left transition-all duration-200"
                      style={{
                        borderColor: role === r.value ? '#0ea5e9' : '#e2e8f0',
                        background:  role === r.value ? 'linear-gradient(135deg,#f0f9ff,#e0f7fa)' : '#fff',
                        boxShadow:   role === r.value ? '0 4px 16px rgba(14,165,233,0.15)' : 'none',
                        transform:   role === r.value ? 'scale(1.01)' : 'scale(1)',
                      }}
                    >
                      <span style={{ fontSize: 28, flexShrink: 0 }}>{r.icon}</span>
                      <div className="flex-1 min-w-0">
                        <div className="font-bold text-slate-800 text-sm">{r.label}</div>
                        <div className="text-xs text-slate-500 mt-0.5">{r.desc}</div>
                      </div>
                      <div style={{
                        width: 20, height: 20, borderRadius: '50%', flexShrink: 0,
                        border: `2px solid ${role === r.value ? '#0ea5e9' : '#cbd5e1'}`,
                        background: role === r.value ? '#0ea5e9' : 'transparent',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        transition: 'all 0.2s ease',
                      }}>
                        {role === r.value && (
                          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="20 6 9 17 4 12" />
                          </svg>
                        )}
                      </div>
                    </button>
                  ))}

                  <div className="flex gap-3 mt-2">
                    <button type="button" onClick={() => setStep(1)}
                      className="btn-secondary flex-1 py-3">
                      ← Back
                    </button>
                    <button type="submit" disabled={!step2Valid}
                      className="btn-primary flex-1 py-3">
                      Continue →
                    </button>
                  </div>
                </div>
              )}

              {/* ── STEP 3: Password ─── */}
              {step === 3 && (
                <div className="space-y-4 animate-fade-in">
                  <div>
                    <label className="input-label" htmlFor="reg-password">Password</label>
                    <div className="relative">
                      <input
                        id="reg-password"
                        type={showPwd ? 'text' : 'password'}
                        value={password} autoFocus
                        onChange={e => setPassword(e.target.value)}
                        className="input-field pr-12" placeholder="Min. 8 characters" required minLength={8}
                      />
                      <button type="button" onClick={() => setShowPwd(v => !v)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-ocean-600 transition-colors text-sm font-medium">
                        {showPwd ? 'Hide' : 'Show'}
                      </button>
                    </div>

                    {/* Password strength bar */}
                    {password.length > 0 && (
                      <div className="mt-2">
                        <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full rounded-full transition-all duration-500"
                            style={{ width: strength.width, background: strength.color }} />
                        </div>
                        <div className="flex justify-between mt-1">
                          <span className="text-[11px] text-slate-400">Password strength</span>
                          <span className="text-[11px] font-bold" style={{ color: strength.color }}>
                            {strength.label}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="input-label" htmlFor="reg-confirm">Confirm password</label>
                    <div className="relative">
                      <input
                        id="reg-confirm"
                        type={showConf ? 'text' : 'password'}
                        value={confirm}
                        onChange={e => setConfirm(e.target.value)}
                        className="input-field pr-12"
                        style={{
                          borderColor: confirm.length > 0 ? (pwMatch ? '#22c55e' : '#ef4444') : undefined,
                          boxShadow: confirm.length > 0 ? (pwMatch ? '0 0 0 3px rgba(34,197,94,0.12)' : '0 0 0 3px rgba(239,68,68,0.12)') : undefined,
                        }}
                        placeholder="Re-enter password" required
                      />
                      <button type="button" onClick={() => setShowConf(v => !v)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-ocean-600 transition-colors text-sm font-medium">
                        {showConf ? 'Hide' : 'Show'}
                      </button>
                    </div>
                    {confirm.length > 0 && !pwMatch && (
                      <p className="text-xs text-red-500 mt-1 font-medium">Passwords do not match</p>
                    )}
                    {pwMatch && (
                      <p className="text-xs text-emerald-600 mt-1 font-medium">Passwords match</p>
                    )}
                  </div>

                  {/* Password rules */}
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 space-y-1.5">
                    {[
                      { rule: password.length >= 8,          text: 'At least 8 characters' },
                      { rule: /[A-Z]/.test(password),        text: 'One uppercase letter' },
                      { rule: /[0-9]/.test(password),        text: 'One number' },
                      { rule: /[^A-Za-z0-9]/.test(password), text: 'One special character (!@#$…)' },
                    ].map(({ rule, text }) => (
                      <div key={text} className="flex items-center gap-2">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                          stroke={rule ? '#22c55e' : '#cbd5e1'} strokeWidth="2.5"
                          strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                        <span className="text-xs" style={{ color: rule ? '#15803d' : '#94a3b8' }}>{text}</span>
                      </div>
                    ))}
                  </div>

                  {/* Terms */}
                  <p className="text-xs text-slate-400 text-center leading-relaxed">
                    By creating an account you agree to our{' '}
                    <span className="text-ocean-600 font-medium cursor-pointer hover:underline">Terms of Service</span>{' '}
                    and{' '}
                    <span className="text-ocean-600 font-medium cursor-pointer hover:underline">Privacy Policy</span>.
                  </p>

                  <div className="flex gap-3">
                    <button type="button" onClick={() => { setStep(2); setError('') }}
                      className="btn-secondary flex-1 py-3">
                      ← Back
                    </button>
                    <button type="submit"
                      disabled={!step3Valid || registerMutation.isPending}
                      className="btn-primary flex-1 py-3 text-base">
                      {registerMutation.isPending
                        ? <><span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" /> Creating…</>
                        : 'Create Account'}
                    </button>
                  </div>
                </div>
              )}
            </form>

            {/* Summary badge (step 2+) */}
            {step > 1 && (
              <div className="mt-5 p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-center gap-3 animate-fade-in">
                <div className="w-9 h-9 rounded-xl flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
                  style={{ background: 'linear-gradient(135deg,#0ea5e9,#14b8a6)' }}>
                  {firstName.charAt(0).toUpperCase()}{lastName.charAt(0).toUpperCase()}
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-slate-700 truncate">{firstName} {lastName}</div>
                  <div className="text-xs text-slate-400 truncate">{email}</div>
                </div>
                {step > 2 && (
                  <span className="ml-auto text-xs font-bold px-2 py-1 rounded-full capitalize"
                    style={{ background: '#f0f9ff', color: '#0369a1', border: '1px solid #bae6fd' }}>
                    {role}
                  </span>
                )}
              </div>
            )}

            {/* Login link */}
            <p className="text-center text-sm text-slate-500 mt-5">
              Already have an account?{' '}
              <Link to="/login"
                className="font-semibold hover:underline"
                style={{ color: '#0ea5e9' }}>
                Sign in →
              </Link>
            </p>
          </div>
        </div>

        <p className="text-center text-xs text-white/80 mt-4 drop-shadow">
          GHG Protocol Compliant · SOC 2 Ready · Enterprise Grade
        </p>
      </div>
    </div>
  )
}
