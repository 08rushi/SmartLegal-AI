import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { registerUser, loginWithGoogle, clearAuthError } from '../store/authSlice'

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: object) => void
          renderButton: (el: HTMLElement, config: object) => void
          prompt: () => void
        }
      }
    }
  }
}

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

export default function Register() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { isLoading, error, token } = useAppSelector((s) => s.auth)
  const googleBtnRef = useRef<HTMLDivElement>(null)

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  useEffect(() => {
    if (token) navigate('/upload', { replace: true })
  }, [token, navigate])

  useEffect(() => {
    dispatch(clearAuthError())
  }, [dispatch])

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return

    const scriptId = 'google-gsi'
    if (document.getElementById(scriptId)) {
      initGoogle()
      return
    }

    const script = document.createElement('script')
    script.id = scriptId
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.defer = true
    script.onload = initGoogle
    document.head.appendChild(script)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function initGoogle() {
    if (!window.google || !googleBtnRef.current) return
    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: handleGoogleCallback,
    })
    window.google.accounts.id.renderButton(googleBtnRef.current, {
      theme: 'outline',
      size: 'large',
      width: '100%',
      text: 'signup_with',
    })
  }

  async function handleGoogleCallback(response: { credential: string }) {
    await dispatch(loginWithGoogle(response.credential))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name || !email || !password) return
    await dispatch(registerUser({ name, email, password }))
  }

  return (
    <div className="content-wrap py-8 sm:py-12">
      <div className="mx-auto grid max-w-6xl overflow-hidden rounded-[34px] border border-white/10 bg-[linear-gradient(180deg,rgba(15,22,38,0.94),rgba(11,18,31,0.92))] shadow-[0_30px_70px_rgba(0,0,0,0.35)] lg:grid-cols-[1.02fr_0.98fr]">

        {/* Left form */}
        <div className="p-6 sm:p-8 lg:p-10">
          <div className="mx-auto max-w-md">
            <p className="text-sm uppercase tracking-[0.26em] text-slate-500">Create Account</p>
            <h1 className="mt-4 text-3xl font-semibold text-white">Start your legal review workspace.</h1>
            <p className="mt-3 text-sm leading-7 text-slate-400">
              Save upload history, revisit analysis dashboards, and keep your question threads in one place.
            </p>

            {error && (
              <div className="mt-5 rounded-[18px] border border-[#fb7185]/25 bg-[#2a1320]/65 px-4 py-3 text-sm text-[#fecdd3]">
                {error}
              </div>
            )}

            {/* Google Sign-Up */}
            <div className="mt-7">
              {GOOGLE_CLIENT_ID ? (
                <div ref={googleBtnRef} className="w-full" />
              ) : (
                <button
                  type="button"
                  disabled
                  className="flex w-full items-center justify-center gap-3 rounded-2xl border border-white/15 bg-white/[0.04] py-3 text-sm text-slate-400"
                >
                  <GoogleIcon />
                  Continue with Google
                  <span className="ml-auto text-xs text-slate-600">(configure client ID)</span>
                </button>
              )}
            </div>

            <div className="my-6 flex items-center gap-3">
              <div className="h-px flex-1 bg-white/10" />
              <span className="text-xs text-slate-600">or create with email</span>
              <div className="h-px flex-1 bg-white/10" />
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="mb-2 block text-sm text-slate-400">Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter your full name"
                  required
                  autoComplete="name"
                  className="input-field"
                />
              </div>
              <div>
                <label className="mb-2 block text-sm text-slate-400">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  required
                  autoComplete="email"
                  className="input-field"
                />
              </div>
              <div>
                <label className="mb-2 block text-sm text-slate-400">Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Create a password (min 8 chars)"
                    required
                    minLength={8}
                    autoComplete="new-password"
                    className="input-field pr-12"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-500 hover:text-slate-300"
                  >
                    {showPassword ? 'Hide' : 'Show'}
                  </button>
                </div>
              </div>
              <button
                type="submit"
                disabled={isLoading || !name || !email || !password}
                className="btn-primary w-full justify-center py-3.5 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isLoading ? (
                  <span className="flex items-center gap-2">
                    <Spinner />
                    Creating account...
                  </span>
                ) : (
                  'Create Account →'
                )}
              </button>
            </form>

            <p className="mt-5 text-sm text-slate-400">
              Already have an account?{' '}
              <Link to="/login" className="text-[#f5c26b] transition hover:text-white">
                Sign in
              </Link>
            </p>

            <p className="mt-6 text-xs leading-6 text-slate-600">
              By creating an account you agree to our Terms of Service and Privacy Policy. Your documents are never stored permanently.
            </p>
          </div>
        </div>

        {/* Right decorative */}
        <div className="relative hidden min-h-[620px] overflow-hidden border-l border-white/10 lg:block">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom,rgba(245,194,107,0.16),transparent_35%),radial-gradient(circle_at_top,rgba(124,58,237,0.18),transparent_40%),linear-gradient(180deg,#0b1120,#090d17)]" />
          <div className="relative z-10 flex h-full flex-col justify-between p-10">
            <div>
              <p className="text-sm uppercase tracking-[0.26em] text-slate-500">Premium Access</p>
              <h2 className="mt-5 max-w-sm text-5xl font-semibold leading-tight text-white">
                Keep every insight, risk flag, and AI answer in one account.
              </h2>
            </div>
            <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6">
              <div className="grid gap-4">
                {['Saved document history', 'Persistent AI Q&A threads', 'Risk analysis reports', 'Hindi + English support'].map((item) => (
                  <div key={item} className="flex items-center gap-3 rounded-[20px] border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-slate-300">
                    <span className="text-[#34d399]">✓</span>
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <path d="M17.64 9.205c0-.639-.057-1.252-.164-1.841H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615Z" fill="#4285F4"/>
      <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18Z" fill="#34A853"/>
      <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332Z" fill="#FBBC05"/>
      <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58Z" fill="#EA4335"/>
    </svg>
  )
}

function Spinner() {
  return (
    <svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeOpacity="0.25" />
      <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  )
}