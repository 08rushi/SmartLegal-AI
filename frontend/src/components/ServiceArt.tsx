/**
 * ServiceArt — per-service-type decorative illustrations for the civic Hub cards.
 *
 * Each service key renders its own illustration, built with the same visual
 * language as the home-page hero: gradient-filled glass surfaces, layered blurred
 * colour glows, soft drop shadows, a light sheen, an "AI scan" line, glowing accent
 * details and a few floating orbs — so the cards read as premium and distinct rather
 * than flat line-art. Purely decorative (the container carries aria-hidden).
 */

import { paletteFor, type Hub, type ServicePalette as P } from '../lib/serviceColors'
import { IllustrationFrame, Panel, Paper, Card, House, Glow, Stamp, PANEL_STROKE, TOP_HL, LINE } from './illustrationKit'

interface ServiceArtProps {
  hub: Hub
  serviceKey: string
  className?: string
  /** SVG preserveAspectRatio — corner-anchored on cards, centred elsewhere. */
  preserve?: string
}

export default function ServiceArt({ hub, serviceKey, className = 'hub-service-svg', preserve }: ServiceArtProps) {
  const p = paletteFor(hub, serviceKey)
  const uid = `${hub}-${serviceKey}`.replace(/[^a-z0-9-]/gi, '')
  return (
    <IllustrationFrame uid={uid} p={p} className={className} preserve={preserve}>
      {renderIcon(hub, serviceKey, p, uid)}
    </IllustrationFrame>
  )
}

/* ── Icon router ─────────────────────────────────────────────────────── */

function renderIcon(hub: Hub, key: string, p: P, uid: string) {
  const acc = `url(#acc-${uid})`

  switch (`${hub}/${key}`) {
    /* ── PROPERTY ─────────────────────────────────────────────────── */
    case 'property/sale':
      return (
        <>
          <House uid={uid} p={p} />
          <Glow uid={uid}>
            <circle cx="150" cy="118" r="23" fill="rgba(6,11,20,0.5)" stroke={acc} strokeWidth="2.8" />
            <circle cx="150" cy="118" r="17" fill="none" stroke={p.accent} strokeWidth="1.4" strokeDasharray="2 3" />
            <text x="150" y="127" textAnchor="middle" fill={acc} fontSize="23" fontWeight="700" fontFamily="Poppins, Inter, sans-serif">
              ₹
            </text>
          </Glow>
        </>
      )

    case 'property/rental':
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

    case 'property/mutation':
      return (
        <>
          <House uid={uid} p={p} />
          <Glow uid={uid}>
            <g stroke={acc} strokeWidth="3.4" fill="none" strokeLinecap="round" strokeLinejoin="round">
              <path d="M126 100 h34" />
              <path d="M152 92 l10 8 -10 8" />
              <path d="M160 124 h-34" />
              <path d="M134 116 l-10 8 10 8" />
            </g>
          </Glow>
        </>
      )

    case 'property/registration':
      return (
        <>
          <House uid={uid} p={p} />
          <Stamp uid={uid} p={p} cx={150} cy={116} r={22} />
        </>
      )

    case 'property/encumbrance':
    case 'property/index_ii':
      return (
        <>
          <Paper uid={uid} x={46} y={26} w={82} h={104} />
          <Glow uid={uid}>
            <g stroke={acc} strokeWidth="3.6" fill="none" strokeLinecap="round">
              <circle cx="120" cy="108" r="22" fill="rgba(6,11,20,0.42)" />
              <line x1="136" y1="124" x2="158" y2="146" />
            </g>
            <path d="M112 108l6 6 12-14" stroke={p.accent} strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </Glow>
        </>
      )

    case 'property/7/12':
      return (
        <>
          <Paper uid={uid} x={48} y={26} w={86} h={106} lines={false} />
          <Glow uid={uid}>
            <text x="91" y="58" textAnchor="middle" fill={acc} fontSize="22" fontWeight="700" fontFamily="Poppins, Inter, sans-serif">
              7/12
            </text>
          </Glow>
          <g stroke={LINE} strokeWidth="2" fill="none">
            <rect x="60" y="74" width="62" height="46" rx="2" />
            <line x1="60" y1="89" x2="122" y2="89" />
            <line x1="60" y1="104" x2="122" y2="104" />
            <line x1="81" y1="74" x2="81" y2="120" />
            <line x1="101" y1="74" x2="101" y2="120" />
          </g>
          <path d="M60 74 l20 15 21 -8 21 12" stroke={acc} strokeWidth="2.6" fill="none" strokeLinecap="round" strokeLinejoin="round" />
        </>
      )

    case 'property/ferfar':
      return (
        <g strokeLinejoin="round">
          <path d="M44 56 l38 -10 40 12 34 -10 v66 l-34 10 -40 -12 -38 10 Z" fill={`url(#surf-${uid})`} stroke={PANEL_STROKE} strokeWidth="1.3" />
          <path d="M44 56 l38 -10 40 12 34 -10" fill="none" stroke={TOP_HL} strokeWidth="1.2" />
          <path d="M82 46 v66" stroke={LINE} strokeWidth="2" strokeDasharray="4 4" fill="none" />
          <path d="M122 58 v66" stroke={LINE} strokeWidth="2" strokeDasharray="4 4" fill="none" />
          <Glow uid={uid}>
            <polygon points="62,70 96,64 110,90 84,106 60,94" fill="rgba(6,11,20,0.3)" stroke={`url(#acc-${uid})`} strokeWidth="2.8" />
            <circle cx="96" cy="64" r="3" fill={p.accent} />
            <circle cx="110" cy="90" r="3" fill={p.accent} />
          </Glow>
        </g>
      )

    /* ── BUSINESS ─────────────────────────────────────────────────── */
    case 'business/gst':
      return (
        <>
          <Paper uid={uid} x={44} y={26} w={84} h={106} lines={false} />
          <line x1="58" y1="48" x2="114" y2="48" stroke={LINE} strokeWidth="3" strokeLinecap="round" />
          <Glow uid={uid}>
            <text x="86" y="94" textAnchor="middle" fill={acc} fontSize="31" fontWeight="700" fontFamily="Poppins, Inter, sans-serif" letterSpacing="1">
              GST
            </text>
          </Glow>
          <line x1="58" y1="116" x2="100" y2="116" stroke={LINE} strokeWidth="3" strokeLinecap="round" />
          <Stamp uid={uid} p={p} cx={142} cy={120} r={21} />
        </>
      )

    case 'business/fssai':
      return (
        <>
          <circle cx="92" cy="92" r="42" fill={`url(#surf-${uid})`} stroke={PANEL_STROKE} strokeWidth="1.3" />
          <path d="M62 62 a42 42 0 0 1 52 4" fill="none" stroke={TOP_HL} strokeWidth="1.2" strokeLinecap="round" />
          <circle cx="92" cy="92" r="27" fill="none" stroke={LINE} strokeWidth="2" />
          <g stroke="rgba(226,232,240,0.6)" strokeWidth="2.6" strokeLinecap="round">
            <line x1="52" y1="66" x2="52" y2="116" />
            <line x1="47" y1="66" x2="47" y2="84" />
            <line x1="57" y1="66" x2="57" y2="84" />
            <path d="M132 66 q8 4 0 22 v26" fill="none" />
          </g>
          <Glow uid={uid}>
            <circle cx="140" cy="120" r="17" fill="rgba(6,11,20,0.45)" stroke={acc} strokeWidth="2.8" />
            <path d="M132 120l6 6 11-13" stroke={p.accent} strokeWidth="3.2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </Glow>
        </>
      )

    case 'business/msme':
      return (
        <>
          <g strokeLinejoin="round">
            <path d="M52 94 l14 -14 v14 M66 94 l14 -14 v14 M80 94 l14 -14 v14 h40 v52 h-92 Z" fill={`url(#surf-${uid})`} stroke={PANEL_STROKE} strokeWidth="1.3" />
            <rect x="120" y="64" width="12" height="30" rx="2" fill={`url(#chip-${uid})`} stroke={PANEL_STROKE} strokeWidth="1.1" />
          </g>
          <g fill="rgba(6,11,20,0.5)" stroke="rgba(255,255,255,0.16)" strokeWidth="1.4">
            <rect x="62" y="108" width="14" height="16" rx="1.5" />
            <rect x="86" y="108" width="14" height="16" rx="1.5" />
            <rect x="110" y="108" width="14" height="16" rx="1.5" />
          </g>
          <Glow uid={uid}>
            <g transform="translate(148,100)">
              <circle r="15" fill="rgba(6,11,20,0.5)" stroke={acc} strokeWidth="2.8" />
              <circle r="5" fill="none" stroke={p.accent} strokeWidth="2.4" />
              {[0, 60, 120, 180, 240, 300].map((deg) => (
                <rect key={deg} x="-2.4" y="-18" width="4.8" height="6" rx="1.5" fill={p.accent} transform={`rotate(${deg})`} />
              ))}
            </g>
          </Glow>
        </>
      )

    case 'business/shop_establishment':
      return (
        <>
          <Panel x={50} y={84} w={100} h={62} rx={4} uid={uid} />
          <rect x="60" y="102" width="30" height="44" rx="1.5" fill="rgba(6,11,20,0.6)" stroke="rgba(255,255,255,0.14)" strokeWidth="1.1" />
          <rect x="104" y="102" width="34" height="26" rx="2" fill={`url(#chip-${uid})`} stroke="rgba(255,255,255,0.14)" strokeWidth="1.1" />
          <g>
            <path d="M46 64 h108 v14 l-6 8 -6 -8 -6 8 -6 -8 -6 8 -6 -8 -6 8 -6 -8 -6 8 -6 -8 -6 8 -6 -8 -6 8 -6 -8 -6 8 -6 -8 -6 8 -6 -8 v-14 Z" fill={`url(#surf-${uid})`} stroke={PANEL_STROKE} strokeWidth="1.2" strokeLinejoin="round" />
            <g stroke={acc} strokeWidth="3.2" opacity="0.85" filter={`url(#aglow-${uid})`}>
              <path d="M64 64 v22 M82 64 v22 M100 64 v22 M118 64 v22 M136 64 v22" />
            </g>
          </g>
        </>
      )

    case 'business/iec':
      return (
        <>
          <circle cx="96" cy="90" r="40" fill={`url(#surf-${uid})`} stroke={PANEL_STROKE} strokeWidth="1.3" />
          <path d="M66 60 a40 40 0 0 1 52 4" fill="none" stroke={TOP_HL} strokeWidth="1.2" strokeLinecap="round" />
          <g stroke={LINE} strokeWidth="1.8" fill="none">
            <ellipse cx="96" cy="90" rx="18" ry="40" />
            <line x1="56" y1="90" x2="136" y2="90" />
            <path d="M60 72 h72 M60 108 h72" />
          </g>
          <Glow uid={uid}>
            <g stroke={acc} strokeWidth="3.4" fill="none" strokeLinecap="round" strokeLinejoin="round">
              <path d="M132 56 a44 44 0 0 1 18 30" />
              <path d="M150 72 l2 16 -15 -6" />
              <path d="M60 124 a44 44 0 0 1 -18 -30" />
              <path d="M42 108 l-2 -16 15 6" />
            </g>
          </Glow>
        </>
      )

    case 'business/trade_license':
      return (
        <>
          <Paper uid={uid} x={46} y={28} w={92} h={98} lines={false} />
          <rect x="62" y="48" width="60" height="30" rx="2" fill={`url(#chip-${uid})`} stroke="rgba(255,255,255,0.16)" strokeWidth="1.1" />
          <path d="M60 48 h64 v8 l-6 6 -6 -6 -6 6 -6 -6 -6 6 -6 -6 -6 6 -6 -6 -6 6 -6 -6 z" fill={`url(#surf-${uid})`} stroke="rgba(255,255,255,0.16)" strokeWidth="1.1" strokeLinejoin="round" />
          <line x1="62" y1="94" x2="122" y2="94" stroke={LINE} strokeWidth="3" strokeLinecap="round" />
          <line x1="62" y1="106" x2="108" y2="106" stroke={LINE} strokeWidth="3" strokeLinecap="round" />
          <Glow uid={uid}>
            <path d="M140 118 l-6 26 8 -5 8 5 -6 -26 z" fill={`url(#acc-${uid})`} />
            <circle cx="144" cy="112" r="13" fill="rgba(6,11,20,0.5)" stroke={acc} strokeWidth="2.6" />
            <path d="M138 112l4 4 8-9" stroke={p.accent} strokeWidth="2.8" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </Glow>
        </>
      )

    case 'business/professional_tax':
      return (
        <>
          <path d="M74 74 h26 v-10 a5 5 0 0 0 -5 -5 h-16 a5 5 0 0 0 -5 5 z" fill={`url(#chip-${uid})`} stroke={PANEL_STROKE} strokeWidth="1.2" strokeLinejoin="round" />
          <Panel x={50} y={72} w={90} h={62} rx={9} uid={uid} />
          <line x1="50" y1="98" x2="140" y2="98" stroke="rgba(255,255,255,0.18)" strokeWidth="1.6" />
          <rect x="84" y="90" width="22" height="12" rx="2" fill={`url(#chip-${uid})`} stroke="rgba(255,255,255,0.16)" strokeWidth="1" />
          <Glow uid={uid}>
            <text x="95" y="126" textAnchor="middle" fill={acc} fontSize="20" fontWeight="700" fontFamily="Poppins, Inter, sans-serif">
              ₹
            </text>
            <circle cx="152" cy="118" r="15" fill="rgba(6,11,20,0.5)" stroke={acc} strokeWidth="2.4" />
            <text x="152" y="124" textAnchor="middle" fill={p.accent} fontSize="15" fontWeight="700" fontFamily="Poppins, Inter, sans-serif">
              ₹
            </text>
          </Glow>
        </>
      )

    case 'business/pan_tan':
      return <Card uid={uid} label="PAN" />

    case 'business/startup_india':
      return (
        <>
          <path d="M100 38 c16 12 20 34 20 52 l-10 12 h-20 l-10 -12 c0 -18 4 -40 20 -52 z" fill={`url(#surf-${uid})`} stroke={PANEL_STROKE} strokeWidth="1.3" strokeLinejoin="round" />
          <path d="M100 38 c9 7 14 18 17 30" fill="none" stroke={TOP_HL} strokeWidth="1.2" strokeLinecap="round" />
          <circle cx="100" cy="74" r="9" fill="rgba(6,11,20,0.55)" stroke={acc} strokeWidth="2.2" />
          <path d="M80 94 c-10 4 -14 14 -14 22 l14 -8 z" fill={`url(#chip-${uid})`} stroke={PANEL_STROKE} strokeWidth="1.1" strokeLinejoin="round" />
          <path d="M120 94 c10 4 14 14 14 22 l-14 -8 z" fill={`url(#chip-${uid})`} stroke={PANEL_STROKE} strokeWidth="1.1" strokeLinejoin="round" />
          <Glow uid={uid}>
            <path d="M90 102 h20 l-4 22 c-2 9 -10 9 -12 0 z" fill={`url(#acc-${uid})`} />
          </Glow>
          <g stroke={acc} strokeWidth="2.4" strokeLinecap="round" opacity="0.85" filter={`url(#aglow-${uid})`}>
            <path d="M60 60 l6 3 M64 78 l7 1 M140 60 l-6 3 M136 78 l-7 1" />
          </g>
        </>
      )

    /* ── LEGAL ID ─────────────────────────────────────────────────── */
    case 'legal-id/aadhaar':
      return (
        <>
          <Card uid={uid} />
          <Glow uid={uid}>
            <g stroke={acc} strokeWidth="2.2" fill="none" strokeLinecap="round">
              <path d="M138 82 a12 12 0 0 1 24 0 v10" />
              <path d="M143 84 a7 7 0 0 1 14 0 v12" />
              <path d="M148 86 a2.5 2.5 0 0 1 5 0 v14" />
              <path d="M134 94 c0 8 2 14 4 18 M162 94 c0 8 -2 14 -4 18" />
            </g>
          </Glow>
        </>
      )

    case 'legal-id/pan':
      return <Card uid={uid} label="PAN" />

    case 'legal-id/driving_licence':
      return (
        <>
          <Panel x={40} y={50} w={122} h={80} rx={10} uid={uid} />
          <line x1="54" y1="68" x2="104" y2="68" stroke={LINE} strokeWidth="3.4" strokeLinecap="round" />
          <line x1="54" y1="80" x2="90" y2="80" stroke={LINE} strokeWidth="3.4" strokeLinecap="round" />
          <Glow uid={uid}>
            <g stroke={acc} strokeWidth="2.6" strokeLinejoin="round" fill="rgba(6,11,20,0.4)">
              <path d="M54 110 l6 -14 h44 l6 14 v8 h-56 z" />
              <path d="M62 96 l4 -8 h30 l4 8" fill="none" />
            </g>
            <circle cx="66" cy="118" r="5" fill="rgba(6,11,20,0.6)" stroke={p.accent} strokeWidth="2.4" />
            <circle cx="100" cy="118" r="5" fill="rgba(6,11,20,0.6)" stroke={p.accent} strokeWidth="2.4" />
            <circle cx="140" cy="88" r="16" fill="none" stroke={acc} strokeWidth="2.6" />
            <circle cx="140" cy="88" r="4" fill={p.accent} />
            <path d="M140 72 v6 M140 98 v6 M124 88 h6 M150 88 h6" stroke={p.accent} strokeWidth="2.4" strokeLinecap="round" />
          </Glow>
        </>
      )

    case 'legal-id/passport':
      return (
        <>
          <Panel x={58} y={28} w={86} h={110} rx={9} uid={uid} />
          <rect x="58" y="28" width="10" height="110" rx="4" fill={`url(#acc-${uid})`} opacity="0.55" />
          <Glow uid={uid}>
            <circle cx="104" cy="80" r="20" fill="none" stroke={acc} strokeWidth="2.4" />
            <g stroke={p.accent} strokeWidth="1.6" fill="none">
              <ellipse cx="104" cy="80" rx="9" ry="20" />
              <line x1="84" y1="80" x2="124" y2="80" />
            </g>
          </Glow>
          <line x1="82" y1="50" x2="126" y2="50" stroke={LINE} strokeWidth="3" strokeLinecap="round" />
          <line x1="80" y1="116" x2="128" y2="116" stroke={LINE} strokeWidth="3" strokeLinecap="round" />
          <line x1="88" y1="126" x2="120" y2="126" stroke={LINE} strokeWidth="3" strokeLinecap="round" />
        </>
      )

    case 'legal-id/voter_id':
      return (
        <>
          <Card uid={uid} />
          <Glow uid={uid}>
            <rect x="128" y="90" width="30" height="30" rx="5" fill="rgba(6,11,20,0.5)" stroke={acc} strokeWidth="2.4" />
            <path d="M134 104l6 7 12-15" stroke={p.accent} strokeWidth="3.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </Glow>
        </>
      )

    case 'legal-id/certificates':
      return (
        <>
          <Paper uid={uid} x={44} y={36} w={94} h={80} />
          <Glow uid={uid}>
            <path d="M96 104 l-6 32 12 -7 12 7 -6 -32 z" fill={`url(#acc-${uid})`} />
            <circle cx="102" cy="100" r="16" fill="rgba(6,11,20,0.5)" stroke={acc} strokeWidth="2.6" />
            <circle cx="102" cy="100" r="9" fill="none" stroke={p.accent} strokeWidth="1.6" strokeDasharray="2 3" />
            <path d="M96 100l4 4 9-10" stroke={p.accent} strokeWidth="2.8" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </Glow>
        </>
      )

    /* ── Fallback ─────────────────────────────────────────────────── */
    default:
      return <Paper uid={uid} />
  }
}
