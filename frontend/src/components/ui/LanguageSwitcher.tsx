import { useTranslation } from 'react-i18next'
import { LANGUAGES, normalizeLanguage, type LanguageCode } from '../../i18n/languages'

interface LanguageSwitcherProps {
  /** "full" = large buttons for the Home page; "compact" = small select for the header. */
  variant?: 'full' | 'compact'
  className?: string
}

/** Global app language switcher (Marathi / Hindi / English, each in its own script). */
export function LanguageSwitcher({ variant = 'full', className = '' }: LanguageSwitcherProps) {
  const { t, i18n } = useTranslation('common')
  const current: LanguageCode = normalizeLanguage(i18n.resolvedLanguage || i18n.language) ?? 'en'
  const compact = variant === 'compact'

  // Compact (header) keeps the original language-selector look: a small dark select with a globe.
  if (compact) {
    return (
      <div className={`flex h-11 items-center gap-1.5 whitespace-nowrap rounded-2xl border border-white/15 bg-white/[0.04] px-2 transition hover:border-[#f5c26b]/25 ${className}`}>
        <span className="pl-1 text-sm text-slate-400" aria-hidden="true">
          🌐
        </span>
        <select
          value={current}
          aria-label={t('language.label')}
          onChange={(e) => void i18n.changeLanguage(e.target.value)}
          className="cursor-pointer bg-transparent pr-1 text-sm font-semibold text-amber-300 focus:outline-none"
        >
          {LANGUAGES.map((lang) => (
            <option key={lang.code} value={lang.code} lang={lang.code} className="bg-slate-900 text-white">
              {lang.nativeName}
            </option>
          ))}
        </select>
      </div>
    )
  }

  return (
    <div
      role="group"
      aria-label={t('language.label')}
      className={`inline-flex items-center gap-1 rounded-2xl border border-white/10 bg-white/[0.04] p-1 ${className}`}
    >
      {LANGUAGES.map((lang) => {
        const active = lang.code === current
        return (
          <button
            key={lang.code}
            type="button"
            lang={lang.code}
            aria-pressed={active}
            title={lang.englishName}
            onClick={() => void i18n.changeLanguage(lang.code)}
            className={`rounded-xl font-medium transition-all duration-200 ${
              'px-5 py-2.5 text-base sm:px-7'
            } ${active ? 'bg-[#f5c26b] font-semibold text-slate-950' : 'text-slate-300 hover:bg-white/5 hover:text-white'}`}
          >
            {lang.nativeName}
          </button>
        )
      })}
    </div>
  )
}

export default LanguageSwitcher
