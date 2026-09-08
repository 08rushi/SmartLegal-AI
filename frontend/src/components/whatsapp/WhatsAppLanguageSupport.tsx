const languages = [
  { code: 'EN', name: 'English', native: 'English', desc: 'Full legal analysis and plain-language answers' },
  { code: 'HI', name: 'Hindi', native: 'हिंदी', desc: 'विधिक प्रश्नों के सरल हिंदी उत्तर एवं विश्लेषण' },
  { code: 'MR', name: 'Marathi', native: 'मराठी', desc: 'कायदेशीर प्रश्नांची सोप्या मराठीत उत्तरे व विश्लेषण' },
]

export default function WhatsAppLanguageSupport() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h2 className="text-2xl font-bold text-white tracking-tight">
          Multilingual Assistance
        </h2>
        <p className="text-sm text-slate-400">
          SmartLegal-AI supports three onboarding languages on WhatsApp. Type <code className="text-amber-400">language</code> anytime to switch.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {languages.map((lang) => (
          <div
            key={lang.code}
            className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 space-y-2"
          >
            <div className="flex items-center justify-between">
              <span className="rounded-md border border-amber-400/30 bg-amber-400/10 px-2 py-0.5 text-xs font-bold text-amber-400">
                {lang.code}
              </span>
              <span className="text-base font-bold text-white">{lang.native}</span>
            </div>
            <h3 className="text-sm font-semibold text-slate-200">{lang.name}</h3>
            <p className="text-xs text-slate-400 leading-relaxed">{lang.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
