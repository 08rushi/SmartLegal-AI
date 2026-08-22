/**
 * CategoryArt — glassmorphic illustrations for the service-category cards (the six
 * hub/overview cards on the Service Center, and the navbar Services dropdown).
 *
 * Shares the exact visual language of ServiceArt via illustrationKit, but keyed by
 * category (legal-id, property, business, tracker, documents, chat, all) instead of a
 * specific service. Purely decorative.
 */

import { categoryPalette, type Category } from '../lib/serviceColors'
import { IllustrationFrame, Panel, Paper, Card, House, Glow, PANEL_STROKE, TOP_HL, LINE } from './illustrationKit'

interface CategoryArtProps {
  art: Category
  className?: string
  /** SVG preserveAspectRatio — corner-anchored on cards, centred for compact icons. */
  preserve?: string
}

export default function CategoryArt({ art, className, preserve }: CategoryArtProps) {
  const p = categoryPalette(art)
  const uid = `cat-${art}`.replace(/[^a-z0-9-]/gi, '')
  return (
    <IllustrationFrame uid={uid} p={p} className={className} preserve={preserve}>
      {renderCategory(art, p, uid)}
    </IllustrationFrame>
  )
}

type P = ReturnType<typeof categoryPalette>

function renderCategory(art: Category, p: P, uid: string) {
  const acc = `url(#acc-${uid})`

  switch (art) {
    /* Legal ID Hub — an ID card with a fingerprint. */
    case 'legal-id':
      return (
        <>
          <Card uid={uid} label="ID" />
          <Glow uid={uid}>
            <g stroke={acc} strokeWidth="2.2" fill="none" strokeLinecap="round">
              <path d="M138 96 a11 11 0 0 1 22 0 v8" />
              <path d="M143 97 a6 6 0 0 1 12 0 v11" />
              <path d="M148 99 a2 2 0 0 1 4 0 v12" />
              <path d="M134 106 c0 7 2 12 3 16 M164 106 c0 7 -2 12 -3 16" />
            </g>
          </Glow>
        </>
      )

    /* Property Hub — a house with a key. */
    case 'property':
      return (
        <>
          <House uid={uid} p={p} />
          <Glow uid={uid}>
            <g stroke={acc} strokeWidth="3.4" fill="none" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="142" cy="104" r="12" fill="rgba(6,11,20,0.4)" />
              <line x1="150" y1="113" x2="173" y2="139" />
              <line x1="164" y1="129" x2="172" y2="121" />
              <line x1="171" y1="137" x2="179" y2="129" />
            </g>
            <circle cx="142" cy="104" r="4" fill={p.accent} />
          </Glow>
        </>
      )

    /* Business License Hub — a storefront with a striped awning. */
    case 'business':
      return (
        <>
          <Panel x={50} y={84} w={100} h={62} rx={4} uid={uid} />
          <rect x="60" y="102" width="30" height="44" rx="1.5" fill="rgba(6,11,20,0.6)" stroke="rgba(255,255,255,0.14)" strokeWidth="1.1" />
          <rect x="104" y="102" width="34" height="26" rx="2" fill={`url(#chip-${uid})`} stroke="rgba(255,255,255,0.14)" strokeWidth="1.1" />
          <path d="M46 64 h108 v14 l-6 8 -6 -8 -6 8 -6 -8 -6 8 -6 -8 -6 8 -6 -8 -6 8 -6 -8 -6 8 -6 -8 -6 8 -6 -8 -6 8 -6 -8 -6 8 -6 -8 v-14 Z" fill={`url(#surf-${uid})`} stroke={PANEL_STROKE} strokeWidth="1.2" strokeLinejoin="round" />
          <g stroke={acc} strokeWidth="3.2" opacity="0.85" filter={`url(#aglow-${uid})`}>
            <path d="M64 64 v22 M82 64 v22 M100 64 v22 M118 64 v22 M136 64 v22" />
          </g>
        </>
      )

    /* Service Tracker — a checklist clipboard with a reminder bell. */
    case 'tracker':
      return (
        <>
          <Panel x={46} y={34} w={92} h={112} rx={9} uid={uid} />
          <rect x="78" y="28" width="28" height="14" rx="3" fill={`url(#chip-${uid})`} stroke={PANEL_STROKE} strokeWidth="1.1" />
          {[0, 1, 2].map((i) => (
            <g key={i}>
              <rect x="58" y={58 + i * 26} width="16" height="16" rx="3.5" fill="rgba(6,11,20,0.5)" stroke={i < 2 ? p.accent : 'rgba(255,255,255,0.22)'} strokeWidth="1.8" />
              {i < 2 && <path d={`M61 ${66 + i * 26} l3.5 3.5 l6 -7`} stroke={p.accent} strokeWidth="2.2" fill="none" strokeLinecap="round" strokeLinejoin="round" />}
              <line x1="82" y1={66 + i * 26} x2={118 - i * 6} y2={66 + i * 26} stroke={LINE} strokeWidth="3" strokeLinecap="round" />
            </g>
          ))}
          <Glow uid={uid}>
            <path d="M150 84 v-3 a2 2 0 0 1 4 0 v3 c8 3 9 12 9 20 l3 5 h-28 l3 -5 c0 -8 1 -17 9 -20 z" fill="rgba(6,11,20,0.5)" stroke={acc} strokeWidth="2.4" strokeLinejoin="round" />
            <path d="M148 112 a4 4 0 0 0 8 0" fill="none" stroke={p.accent} strokeWidth="2.4" strokeLinecap="round" />
          </Glow>
        </>
      )

    /* Document Analysis — a document scanned with a magnifier + risk flag. */
    case 'documents':
      return (
        <>
          <Paper uid={uid} x={46} y={26} w={84} h={110} />
          <Glow uid={uid}>
            <g stroke={acc} strokeWidth="3.6" fill="none" strokeLinecap="round">
              <circle cx="122" cy="106" r="21" fill="rgba(6,11,20,0.42)" />
              <line x1="137" y1="121" x2="159" y2="145" />
            </g>
            <path d="M114 106l6 6 12-14" stroke={p.accent} strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="122" cy="40" r="12" fill="rgba(6,11,20,0.5)" stroke={acc} strokeWidth="2.4" />
            <path d="M122 35 v6" stroke={p.accent} strokeWidth="2.6" strokeLinecap="round" />
            <circle cx="122" cy="45.5" r="1.4" fill={p.accent} />
          </Glow>
        </>
      )

    /* AI Legal Assistant — two chat bubbles. */
    case 'chat':
      return (
        <>
          <g>
            <path d="M44 56 h74 a10 10 0 0 1 10 10 v26 a10 10 0 0 1 -10 10 h-46 l-14 12 v-12 a10 10 0 0 1 -10 -10 v-26 a10 10 0 0 1 10 -10 z" fill={`url(#surf-${uid})`} stroke={PANEL_STROKE} strokeWidth="1.3" strokeLinejoin="round" />
            <line x1="52" y1="66" x2="120" y2="66" stroke={TOP_HL} strokeWidth="1.1" strokeLinecap="round" opacity="0.6" />
            {[0, 1, 2].map((i) => (
              <circle key={i} cx={64 + i * 20} cy="80" r="4.4" fill={i === 0 ? p.accent : 'rgba(226,232,240,0.55)'} />
            ))}
          </g>
          <Glow uid={uid}>
            <path d="M108 100 h48 a10 10 0 0 1 10 10 v20 a10 10 0 0 1 -10 10 h-30 l-12 10 v-10 a10 10 0 0 1 -6 -8 v-24 a8 8 0 0 1 0 -18 z" fill="rgba(6,11,20,0.5)" stroke={acc} strokeWidth="2.2" strokeLinejoin="round" />
            <path d="M124 118 h30 M124 128 h20" stroke={p.accent} strokeWidth="2.6" strokeLinecap="round" />
          </Glow>
        </>
      )

    /* View All Services — a 2×2 grid of tiles. */
    case 'all':
    default:
      return (
        <>
          <Panel x={54} y={48} w={44} h={40} rx={7} uid={uid} />
          <Panel x={108} y={48} w={44} h={40} rx={7} uid={uid} />
          <Panel x={54} y={98} w={44} h={40} rx={7} uid={uid} />
          <Panel x={108} y={98} w={44} h={40} rx={7} uid={uid} />
          <Glow uid={uid}>
            <circle cx="66" cy="60" r="4" fill={p.accent} />
            <circle cx="120" cy="60" r="4" fill={p.accent} />
            <circle cx="66" cy="110" r="4" fill={p.accent} />
            <path d="M118 116 l4 4 8 -9" stroke={p.accent} strokeWidth="2.6" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </Glow>
        </>
      )
  }
}
