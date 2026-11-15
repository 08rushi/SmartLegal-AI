import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAppDispatch } from '../hooks/redux'
import { forgotPassword } from '../store/authSlice'

export default function ForgotPassword() {
  const { t } = useTranslation('auth')
  const dispatch = useAppDispatch()
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const [message, setMessage] = useState('')
  const [devToken, setDevToken] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!email) return
    setLoading(true)
    setError(null)
    try {
      const data = await dispatch(forgotPassword(email)).unwrap()
      setMessage(data.message)
      setDevToken(data.reset_token ?? null)
      setSent(true)
    } catch (err) {
      setError(typeof err === 'string' ? err : t('errors:generic'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="content-wrap py-8 sm:py-12">
      <div className="mx-auto max-w-md rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(15,22,38,0.94),rgba(11,18,31,0.92))] p-7 shadow-[0_30px_70px_rgba(0,0,0,0.35)] sm:p-8">
        <p className="text-sm uppercase tracking-[0.26em] text-slate-500">{t('forgot.eyebrow')}</p>
        <h1 className="mt-3 text-2xl font-semibold text-white">{t('forgot.title')}</h1>
        <p className="mt-2 text-sm leading-7 text-slate-400">
          {t('forgot.body')}
        </p>

        {error && (
          <div id="forgot-error" role="alert" className="mt-5 rounded-[16px] border border-[#fb7185]/25 bg-[#2a1320]/65 px-4 py-3 text-sm text-[#fecdd3]">
            {error}
          </div>
        )}

        {sent ? (
          <div className="mt-6 space-y-4">
            <div className="rounded-[16px] border border-[#34d399]/25 bg-[#0f2a20]/60 px-4 py-3 text-sm text-[#bbf7d0]">
              {message}
            </div>

            {devToken && (
              <div className="rounded-[16px] border border-[#f5c26b]/25 bg-[#20170d]/70 px-4 py-3 text-xs text-[#fde9c8]">
                <p className="font-medium text-[#f5c26b]">{t('forgot.devMode')}</p>
                <p className="mt-1 leading-6">
                  {t('forgot.devBody')}
                </p>
                <Link
                  to={`/reset-password?token=${encodeURIComponent(devToken)}`}
                  className="mt-2 inline-block break-all text-[#f5c26b] underline"
                >
                  {t('forgot.devLink')}
                </Link>
              </div>
            )}

            <Link to="/login" className="btn-secondary w-full justify-center">
              {t('forgot.backToSignIn')}
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label htmlFor="forgot-email" className="mb-2 block text-sm text-slate-400">{t('email')}</label>
              <input
                id="forgot-email"
                aria-describedby={error ? 'forgot-error' : undefined}
                aria-invalid={error ? true : undefined}
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t('forgot.emailPlaceholder')}
                required
                autoComplete="email"
                className="input-field"
              />
            </div>
            <button
              type="submit"
              disabled={loading || !email}
              className="btn-primary w-full justify-center py-3.5 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? t('forgot.sending') : t('forgot.submit')}
            </button>
            <div className="text-center text-sm">
              <Link to="/login" className="text-slate-400 transition hover:text-[#f5c26b]">
                {t('forgot.backToSignIn')}
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
