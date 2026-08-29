import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAppDispatch } from '../hooks/redux'
import { resetPassword } from '../store/authSlice'

export default function ResetPassword() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const [params] = useSearchParams()

  const [token, setToken] = useState(params.get('token') ?? '')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (!token.trim()) {
      setError('Missing reset token. Please use the link from your reset email.')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true)
    try {
      await dispatch(resetPassword({ token: token.trim(), new_password: password })).unwrap()
      setDone(true)
      setTimeout(() => navigate('/login', { replace: true }), 2500)
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Could not reset your password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="content-wrap py-8 sm:py-12">
      <div className="mx-auto max-w-md rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(15,22,38,0.94),rgba(11,18,31,0.92))] p-7 shadow-[0_30px_70px_rgba(0,0,0,0.35)] sm:p-8">
        <p className="text-sm uppercase tracking-[0.26em] text-slate-500">Password Reset</p>
        <h1 className="mt-3 text-2xl font-semibold text-white">Set a new password</h1>

        {done ? (
          <div className="mt-6 space-y-4">
            <div className="rounded-[16px] border border-[#34d399]/25 bg-[#0f2a20]/60 px-4 py-3 text-sm text-[#bbf7d0]">
              Your password has been reset and all other sessions were signed out. Redirecting to sign in…
            </div>
            <Link to="/login" className="btn-primary w-full justify-center">
              Go to Sign In
            </Link>
          </div>
        ) : (
          <>
            <p className="mt-2 text-sm leading-7 text-slate-400">
              Choose a strong new password. This will also sign you out of all other devices.
            </p>

            {error && (
              <div className="mt-5 rounded-[16px] border border-[#fb7185]/25 bg-[#2a1320]/65 px-4 py-3 text-sm text-[#fecdd3]">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              {!params.get('token') && (
                <div>
                  <label className="mb-2 block text-sm text-slate-400">Reset Token</label>
                  <input
                    type="text"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    placeholder="Paste the token from your reset email"
                    required
                    className="input-field"
                  />
                </div>
              )}
              <div>
                <label className="mb-2 block text-sm text-slate-400">New Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="At least 8 characters"
                    required
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
              <div>
                <label className="mb-2 block text-sm text-slate-400">Confirm New Password</label>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  placeholder="Re-enter your new password"
                  required
                  autoComplete="new-password"
                  className="input-field"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full justify-center py-3.5 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? 'Resetting…' : 'Reset Password'}
              </button>
              <div className="text-center text-sm">
                <Link to="/login" className="text-slate-400 transition hover:text-[#f5c26b]">
                  Back to Sign In
                </Link>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  )
}
