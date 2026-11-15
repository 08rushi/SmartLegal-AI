import { LanguageSwitcher } from './LanguageSwitcher'

export interface LanguageOption {
  code: string
  name: string
  nativeName: string
}

// Kept for backward compatibility. The app-wide switcher only supports mr / hi / en
// (see src/i18n/languages.ts); the other entries are future candidates.
export class LanguageCatalog {
  static LANGUAGES: LanguageOption[] = [
    { code: 'en', name: 'English', nativeName: 'English' },
    { code: 'hi', name: 'Hindi', nativeName: 'हिंदी' },
    { code: 'mr', name: 'Marathi', nativeName: 'मराठी' },
    { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்' },
    { code: 'te', name: 'Telugu', nativeName: 'తెలుగు' },
    { code: 'bn', name: 'Bengali', nativeName: 'বাংলা' },
  ]
}

/** Now a thin wrapper over the global LanguageSwitcher (no local state). */
export function LanguageSelector() {
  return <LanguageSwitcher variant="compact" />
}

export { LanguageSwitcher }
