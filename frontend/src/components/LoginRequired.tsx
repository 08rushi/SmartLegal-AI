import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

/**
 * Friendly "please sign in" prompt shown in place of a protected page, instead of
 * an abrupt redirect. Preserves where the user was headed so they return there
 * after signing in.
 */
export default function LoginRequired({
  title,
  message,
}: {
  /** Already-translated text; when omitted the default prompt (shell:loginRequired.*) is shown. */
  title?: string
  message?: string
}) {
  const { t } = useTranslation('shell')
  const location = useLocation()
  const from = location.pathname + location.search

  return (
    <div className="content-wrap py-10 sm:py-16">
      <div className="mx-auto max-w-md rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(15,22,38,0.94),rgba(11,18,31,0.92))] p-8 text-center shadow-[0_30px_70px_rgba(0,0,0,0.35)]">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-[22px] border border-[#f5c26b]/25 bg-[#f5c26b]/10 text-3xl text-[#f5c26b]">
          🔒
        </div>
        <h1 className="mt-5 text-2xl font-semibold text-white">{title ?? t('loginRequired.title')}</h1>
        <p className="mx-auto mt-2 max-w-sm text-sm leading-7 text-slate-400">{message ?? t('loginRequired.message')}</p>
        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
          <Link to="/login" state={{ from }} className="btn-primary justify-center px-6 py-3">
            {t('loginRequired.signIn')}
          </Link>
          <Link to="/register" state={{ from }} className="btn-secondary justify-center px-6 py-3">
            {t('loginRequired.createAccount')}
          </Link>
        </div>
        <p className="mt-5 text-xs text-slate-600">
          {t('loginRequired.freeNote')}
        </p>
      </div>
    </div>
  )
}
