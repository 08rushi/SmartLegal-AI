import { useEffect, useState, useRef } from 'react'
import { Link } from 'react-router-dom'

function WhatsAppIcon({ className = 'h-6 w-6' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.572-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L0 24l6.335-1.662a11.87 11.87 0 005.708 1.458h.005c6.554 0 11.89-5.335 11.893-11.892a11.821 11.821 0 00-3.477-8.414" />
    </svg>
  )
}

export default function WhatsAppStickyButton() {
  const [isTooltipOpen, setIsTooltipOpen] = useState(false)
  const [isWiggling, setIsWiggling] = useState(false)
  const [isHoveredOrFocused, setIsHoveredOrFocused] = useState(false)
  const [hasClicked, setHasClicked] = useState(false)
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false)

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // 1. Detect prefers-reduced-motion in JavaScript
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    setPrefersReducedMotion(mediaQuery.matches)

    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches)
    }

    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange)
      return () => mediaQuery.removeEventListener('change', handleChange)
    }
  }, [])

  // 2. Automatic Tooltip & Wiggle Cycle (~3s visible / ~2.5s hidden)
  useEffect(() => {
    if (prefersReducedMotion || hasClicked) {
      setIsTooltipOpen(false)
      setIsWiggling(false)
      return
    }

    let isMounted = true

    const runCycle = () => {
      if (!isMounted || hasClicked) return

      // Trigger subtle wiggle animation
      setIsWiggling(true)
      setTimeout(() => {
        if (isMounted) setIsWiggling(false)
      }, 500)

      // Show tooltip for ~3000ms
      setIsTooltipOpen(true)

      timerRef.current = setTimeout(() => {
        if (!isMounted) return
        setIsTooltipOpen(false)

        // Hide tooltip for ~2500ms before repeating
        timerRef.current = setTimeout(() => {
          if (isMounted) runCycle()
        }, 2500)
      }, 3000)
    }

    // Initial delay before first cycle
    timerRef.current = setTimeout(runCycle, 1500)

    return () => {
      isMounted = false
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [prefersReducedMotion, hasClicked])

  const handleClick = () => {
    setHasClicked(true)
    setIsTooltipOpen(false)
    setIsWiggling(false)
    if (timerRef.current) clearTimeout(timerRef.current)
  }

  // Active tooltip status: shown via auto-cycle OR user hover/focus (unless clicked)
  const shouldShowTooltip = !hasClicked && (isTooltipOpen || isHoveredOrFocused)

  return (
    <div className="relative flex items-center justify-end">
      {/* Primary Textual Tooltip */}
      {shouldShowTooltip && (
        <div
          id="whatsapp-cta-tooltip"
          role="tooltip"
          className="absolute right-0 bottom-full mb-3.5 sm:right-full sm:mr-3.5 sm:bottom-auto sm:top-1/2 sm:-translate-y-1/2 z-50 w-48 rounded-xl border border-emerald-500/30 bg-[#0f172a] p-3 text-xs shadow-xl backdrop-blur-md transition-all duration-200 pointer-events-none"
        >
          <div className="flex items-center gap-1.5 font-semibold text-emerald-400">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>Chat on WhatsApp</span>
          </div>
          <p className="mt-0.5 text-slate-300 text-[11px] leading-tight">
            Get legal help instantly.
          </p>
          {/* Pointer Arrow */}
          <div className="hidden sm:block absolute top-1/2 -right-1.5 -translate-y-1/2 border-y-4 border-y-transparent border-l-6 border-l-[#0f172a]" />
          <div className="sm:hidden absolute -bottom-1.5 right-4 border-x-4 border-x-transparent border-t-6 border-t-[#0f172a]" />
        </div>
      )}

      {/* Icon-First Circular Floating Action Button */}
      <Link
        to="/channels/whatsapp"
        aria-label="Chat on WhatsApp"
        aria-describedby={shouldShowTooltip ? 'whatsapp-cta-tooltip' : undefined}
        onClick={handleClick}
        onMouseEnter={() => setIsHoveredOrFocused(true)}
        onMouseLeave={() => setIsHoveredOrFocused(false)}
        onFocus={() => setIsHoveredOrFocused(true)}
        onBlur={() => setIsHoveredOrFocused(false)}
        className={`w-12 h-12 sm:w-[52px] sm:h-[52px] rounded-full flex items-center justify-center border border-emerald-400/40 bg-[linear-gradient(180deg,#25D366,#128C7E)] text-slate-950 shadow-[0_10px_30px_rgba(37,211,102,0.35)] transition duration-200 hover:brightness-110 hover:shadow-[0_14px_35px_rgba(37,211,102,0.45)] focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:ring-offset-2 focus:ring-offset-[#0b0f19] ${
          isWiggling && !prefersReducedMotion ? 'animate-gentle-wiggle' : ''
        }`}
      >
        <WhatsAppIcon className="h-6 w-6 text-slate-950" />
      </Link>
    </div>
  )
}
