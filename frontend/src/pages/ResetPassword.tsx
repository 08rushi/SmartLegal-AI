import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAppDispatch } from '../hooks/redux'
import { resetPassword } from '../store/authSlice'

export default function ResetPassword() {
  const { t } = useTranslation('auth')
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
      setError(t('errors:missingToken'))
      return
    }
    if (password.length < 8) {
      setError(t('errors:passwordTooShort'))
      return
    }
    if (password !== confirm) {
      setError(t('errors:passwordMismatch'))
      return
    }
    setLoading(true)
    try {
      await dispatch(resetPassword({ token: token.trim(), new_password: password })).unwrap()
      setDone(true)
      setTimeout(() => navigate('/login', { replace: true }), 2500)
    } catch (err) {
      setError(typeof err === 'string' ? err : t('errors:resetFailed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="content-wrap py-8 sm:py-12">
      <div className="mx-auto max-w-md rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(15,22,38,0.94),rgba(11,18,31,0.92))] p-7 shadow-[0_30px_70px_rgba(0,0,0,0.35)] sm:p-8">
        <p className="text-sm uppercase tracking-[0.26em] text-slate-500">{t('reset.eyebrow')}</p>
        <h1 className="mt-3 text-2xl font-semibold text-white">{t('reset.title')}</h1>

        {done ? (
          <div className="mt-6 space-y-4">
            <div className="rounded-[16px] border border-[#34d399]/25 bg-[#0f2a20]/60 px-4 py-3 text-sm text-[#bbf7d0]">
              {t('reset.done')}
            </div>
            <Link to="/login" className="btn-primary w-full justify-center">
              {t('reset.goToSignIn')}
            </Link>
          </div>
        ) : (
          <>
            <p className="mt-2 text-sm leading-7 text-slate-400">
              {t('reset.body')}
            </p>

            {error && (
              <div id="reset-error" role="alert" className="mt-5 rounded-[16px] border border-[#fb7185]/25 bg-[#2a1320]/65 px-4 py-3 text-sm text-[#fecdd3]">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              {!params.get('token') && (
                <div>
                  <label htmlFor="reset-token" className="mb-2 block text-sm text-slate-400">{t('reset.token')}</label>
                  <input
                    id="reset-token"
                    aria-describedby={error ? 'reset-error' : undefined}
                    type="text"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    placeholder={t('reset.tokenPlaceholder')}
                    required
                    className="input-field"
                  />
                </div>
              )}
              <div>
                <label htmlFor="reset-password" className="mb-2 block text-sm text-slate-400">{t('reset.newPassword')}</label>
                <div className="relative">
                  <input
                    id="reset-password"
                    aria-describedby={error ? 'reset-error' : undefined}
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={t('reset.newPasswordPlaceholder')}
                    required
                    autoComplete="new-password"
                    className="input-field pr-12"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    aria-pressed={showPassword}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-500 hover:text-slate-300"
                  >
                    {showPassword ? t('common:hide') : t('common:show')}
                  </button>
                </div>
              </div>
              <div>
                <label htmlFor="reset-confirm" className="mb-2 block text-sm text-slate-400">{t('reset.confirm')}</label>
                <input
                  id="reset-confirm"
                  aria-describedby={error ? 'reset-error' : undefined}
                  type={showPassword ? 'text' : 'password'}
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  placeholder={t('reset.confirmPlaceholder')}
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
                {loading ? t('reset.submitting') : t('reset.submit')}
              </button>
              <div className="text-center text-sm">
                <Link to="/login" className="text-slate-400 transition hover:text-[#f5c26b]">
                  {t('reset.backToSignIn')}
                </Link>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  )
}
