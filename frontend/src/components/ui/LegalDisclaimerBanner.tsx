export function LegalDisclaimerBanner() {
  return (
    <div className="bg-[#121a2d]/80 border border-slate-800 rounded-2xl p-4 text-xs text-slate-400 space-y-1 backdrop-blur-xl">
      <div className="flex items-center gap-2 font-bold text-amber-400">
        <span>⚖️</span>
        <span className="uppercase tracking-wider">Important Legal & Regulatory Disclaimer</span>
      </div>
      <p className="leading-relaxed">
        SmartLegal AI provides automated information and document analysis based on Indian laws.
        It does <strong>not</strong> constitute formal legal representation, legal advice, or an attorney-client relationship under the Advocates Act, 1961.
        For high-stakes disputes or litigation, consult a qualified advocate registered with the Bar Council of India.
      </p>
    </div>
  )
}
