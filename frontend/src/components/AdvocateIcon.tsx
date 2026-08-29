/**
 * AdvocateIcon — the lawyer's neck bands (the twin white tabs worn with an
 * advocate's collar), the classic symbol of an Indian/UK lawyer. Drawn with
 * `currentColor` so it inherits the gold theme accent and stays crisp at any size.
 * Decorative by default.
 */
export default function AdvocateIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
      {/* collar opening */}
      <path d="M7.5 4 L12 7 L16.5 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      {/* collar band the tabs hang from */}
      <rect x="9.7" y="6.4" width="4.6" height="1.6" rx="0.6" fill="currentColor" />
      {/* left band (tab) */}
      <path d="M10 7.8 H11.5 V16.6 L10.75 18.7 L10 16.6 Z" fill="currentColor" />
      {/* right band (tab) */}
      <path d="M12.5 7.8 H14 V16.6 L13.25 18.7 L12.5 16.6 Z" fill="currentColor" />
    </svg>
  )
}
