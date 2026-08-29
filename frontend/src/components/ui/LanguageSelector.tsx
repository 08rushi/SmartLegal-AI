import { useState } from 'react'

export interface LanguageOption {
  code: string
  name: string
  nativeName: string
}

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

interface LanguageSelectorProps {
  currentLanguage?: string
  onChange?: (code: string) => void
}

export function LanguageSelector({
  currentLanguage = 'en',
  onChange,
}: LanguageSelectorProps) {
  const [selected, setSelected] = useState(currentLanguage)

  const handleSelect = (code: string) => {
    setSelected(code)
    if (onChange) onChange(code)
  }

  return (
    <div className="flex items-center gap-1.5 bg-slate-900/80 border border-slate-800 p-1 rounded-xl">
      <span className="text-xs text-slate-400 pl-2">🌐</span>
      <select
        value={selected}
        onChange={(e) => handleSelect(e.target.value)}
        className="bg-transparent text-xs font-semibold text-amber-300 focus:outline-none cursor-pointer pr-2"
      >
        {LanguageCatalog.LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code} className="bg-slate-900 text-white">
            {lang.nativeName} ({lang.name})
          </option>
        ))}
      </select>
    </div>
  )
}
