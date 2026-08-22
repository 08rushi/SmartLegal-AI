/**
 * illustrationKit — shared building blocks for the glassmorphic service illustrations.
 *
 * Provides the outer <svg> frame (gradient/filter defs, blurred colour glows, AI-scan
 * line, drop-shadowed + tilted main group, floating orbs) plus reusable primitives
 * (glass Panel, Paper, Card, House, Stamp, Glow). Both ServiceArt (per-service) and
 * CategoryArt (per-category) compose their icons from these so everything shares one
 * visual language, matching the home-page hero.
 */

import type { ReactNode } from 'react'
import type { ServicePalette as P } from '../lib/serviceColors'

export type { P }

export const PANEL_STROKE = 'rgba(255,255,255,0.18)'
export const TOP_HL = 'rgba(255,255,255,0.24)'
export const LINE = 'rgba(226,232,240,0.42)'

/* ── Gradient / filter definitions (unique per illustration instance) ── */
function Defs({ uid, p }: { uid: string; p: P }) {
  return (
    <defs>
      <radialGradient id={`ga-${uid}`} cx="50%" cy="50%" r="50%">
        <stop offset="0%" stopColor={p.echo} />
        <stop offset="100%" stopColor="rgba(0,0,0,0)" />
      </radialGradient>
      <radialGradient id={`gb-${uid}`} cx="50%" cy="50%" r="50%">
        <stop offset="0%" stopColor={p.tint} />
        <stop offset="100%" stopColor="rgba(0,0,0,0)" />
      </radialGradient>
      <linearGradient id={`surf-${uid}`} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor={p.tint} />
        <stop offset="100%" stopColor="rgba(9,13,23,0.96)" />
      </linearGradient>
      <linearGradient id={`chip-${uid}`} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="rgba(255,255,255,0.20)" />
        <stop offset="100%" stopColor="rgba(255,255,255,0.05)" />
      </linearGradient>
      <linearGradient id={`acc-${uid}`} x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor={p.accent} />
        <stop offset="100%" stopColor={p.accent2} />
      </linearGradient>
      <linearGradient id={`sheen-${uid}`} x1="0" y1="0" x2="0.7" y2="1">
        <stop offset="0%" stopColor="rgba(255,255,255,0.14)" />
        <stop offset="46%" stopColor="rgba(255,255,255,0)" />
      </linearGradient>
      <linearGradient id={`scan-${uid}`} x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stopColor="rgba(0,0,0,0)" />
        <stop offset="50%" stopColor={p.accent} />
        <stop offset="100%" stopColor="rgba(0,0,0,0)" />
      </linearGradient>
      <filter id={`blur-${uid}`} x="-60%" y="-60%" width="220%" height="220%">
        <feGaussianBlur stdDeviation="13" />
      </filter>
      <filter id={`shadow-${uid}`} x="-30%" y="-25%" width="160%" height="165%">
        <feDropShadow dx="0" dy="8" stdDeviation="7" floodColor="#04070e" floodOpacity="0.42" />
      </filter>
      <filter id={`aglow-${uid}`} x="-70%" y="-70%" width="240%" height="240%">
        <feDropShadow dx="0" dy="0" stdDeviation="2" floodColor={p.accent} floodOpacity="0.38" />
      </filter>
    </defs>
  )
}

/* Outer frame: defs + glows + scan line + shadowed/tilted content + orbs. */
export function IllustrationFrame({
  uid,
  p,
  children,
  className,
  preserve = 'xMidYMax meet',
  scan = true,
}: {
  uid: string
  p: P
  children: ReactNode
  className?: string
  preserve?: string
  scan?: boolean
}) {
  return (
    <svg viewBox="0 0 206 178" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} preserveAspectRatio={preserve}>
      <Defs uid={uid} p={p} />
      <ellipse cx="126" cy="112" rx="88" ry="72" fill={`url(#ga-${uid})`} filter={`url(#blur-${uid})`} opacity="0.8" />
      <ellipse cx="66" cy="58" rx="58" ry="48" fill={`url(#gb-${uid})`} filter={`url(#blur-${uid})`} opacity="0.8" />
      {scan && <rect x="-10" y="90" width="230" height="2" fill={`url(#scan-${uid})`} opacity="0.28" />}
      <g filter={`url(#shadow-${uid})`} transform="rotate(-3 104 96)">
        {children}
      </g>
      <circle cx="46" cy="42" r="3.4" fill={p.accent} opacity="0.55" />
      <circle cx="176" cy="150" r="2.6" fill={p.accent2} opacity="0.5" />
      <circle cx="30" cy="120" r="2.2" fill={p.accent} opacity="0.4" />
    </svg>
  )
}

/* ── Reusable primitives ─────────────────────────────────────────────── */

/* Frosted glass panel: gradient fill + lit top edge + diagonal sheen. */
export function Panel({ x, y, w, h, rx = 8, uid, chip }: { x: number; y: number; w: number; h: number; rx?: number; uid: string; chip?: boolean }) {
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx={rx} fill={chip ? `url(#chip-${uid})` : `url(#surf-${uid})`} stroke={PANEL_STROKE} strokeWidth="1.3" />
      <rect x={x} y={y} width={w} height={h} rx={rx} fill={`url(#sheen-${uid})`} />
      <line x1={x + rx} y1={y + 1.2} x2={x + w - rx} y2={y + 1.2} stroke={TOP_HL} strokeWidth="1.2" strokeLinecap="round" />
    </g>
  )
}

/* Glowing accent group (neon-ish detail on top of the glass). */
export function Glow({ uid, children }: { uid: string; children: ReactNode }) {
  return <g filter={`url(#aglow-${uid})`}>{children}</g>
}

export function House({ uid, p }: { uid: string; p: P }) {
  return (
    <g>
      <polygon points="52,82 100,44 148,82" fill={`url(#surf-${uid})`} stroke={PANEL_STROKE} strokeWidth="1.3" strokeLinejoin="round" />
      <line x1="52" y1="82" x2="100" y2="44" stroke={TOP_HL} strokeWidth="1.3" strokeLinecap="round" />
      <Panel x={62} y={82} w={76} h={64} rx={6} uid={uid} />
      <rect x="89" y="112" width="22" height="34" rx="2" fill="rgba(6,11,20,0.7)" stroke={PANEL_STROKE} strokeWidth="1.1" />
      <circle cx="105" cy="130" r="1.8" fill={p.accent} />
      <rect x="72" y="93" width="15" height="13" rx="2" fill={`url(#chip-${uid})`} stroke="rgba(255,255,255,0.14)" strokeWidth="1" />
    </g>
  )
}

export function Paper({ uid, x = 52, y = 30, w = 84, h = 108, lines = true }: { uid: string; x?: number; y?: number; w?: number; h?: number; lines?: boolean }) {
  return (
    <g>
      <Panel x={x} y={y} w={w} h={h} rx={7} uid={uid} />
      {lines &&
        [0, 1, 2, 3].map((i) => (
          <line key={i} x1={x + 14} y1={y + 24 + i * 16} x2={x + w - 14 - (i % 2 ? 16 : 0)} y2={y + 24 + i * 16} stroke={LINE} strokeWidth="3" strokeLinecap="round" />
        ))}
    </g>
  )
}

export function Card({ uid, label }: { uid: string; label?: string }) {
  return (
    <g>
      <Panel x={40} y={50} w={122} h={80} rx={10} uid={uid} />
      <rect x="52" y="64" width="34" height="44" rx="6" fill={`url(#chip-${uid})`} stroke="rgba(255,255,255,0.16)" strokeWidth="1.1" />
      <circle cx="69" cy="78" r="8" fill="rgba(226,232,240,0.55)" />
      <path d="M56 104c2-9 24-9 26 0" stroke="rgba(226,232,240,0.55)" strokeWidth="2.4" fill="none" strokeLinecap="round" />
      {label && (
        <Glow uid={uid}>
          <text x="98" y="76" fill={`url(#acc-${uid})`} fontSize="16" fontWeight="700" fontFamily="Poppins, Inter, sans-serif">
            {label}
          </text>
        </Glow>
      )}
      <line x1="98" y1="90" x2="150" y2="90" stroke={LINE} strokeWidth="3.4" strokeLinecap="round" />
      <line x1="98" y1="102" x2="142" y2="102" stroke={LINE} strokeWidth="3.4" strokeLinecap="round" />
      <line x1="98" y1="114" x2="152" y2="114" stroke={LINE} strokeWidth="3.4" strokeLinecap="round" />
    </g>
  )
}

export function Stamp({ uid, p, cx, cy, r = 21 }: { uid: string; p: P; cx: number; cy: number; r?: number }) {
  return (
    <Glow uid={uid}>
      <g transform={`rotate(-15 ${cx} ${cy})`}>
        <circle cx={cx} cy={cy} r={r} fill="rgba(6,11,20,0.35)" stroke={`url(#acc-${uid})`} strokeWidth="2.8" />
        <circle cx={cx} cy={cy} r={r - 5} fill="none" stroke={p.accent} strokeWidth="1.5" strokeDasharray="3 3" />
        <path d={`M${cx - 8} ${cy} l6 6 l10 -12`} stroke={p.accent} strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      </g>
    </Glow>
  )
}
