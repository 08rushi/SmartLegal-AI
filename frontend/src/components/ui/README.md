# UI design system

Goal: easy for low-literacy and first-time users. Flat surfaces, high contrast, big type, big targets, icon + word
everywhere. Tokens live in `src/index.css` (`:root`) and are exposed as Tailwind colours in `tailwind.config.js`.

## Rules
1. **Never colour alone.** Status (risk, success, error) is always icon + word + colour (`RiskPill`, `Notice`).
2. **Touch targets >= 48px.** Buttons, inputs, tabs, icon buttons (`min-h-touch` / `min-w-touch`).
3. **Every visible string is a `t()` key** in en/hi/mr (plain everyday words). Components here take already-translated
   strings as props; the few built-in strings live in the `ui`, `speech` and `nav` namespaces.
4. **Every icon button has an `aria-label`**; icons themselves are `aria-hidden`.
5. **Every overlay uses `Modal`.** Never write `fixed inset-0` by hand (a test enforces this).
6. No blur, gradients or glows. Motion is minimal and disabled by `prefers-reduced-motion`.

## Tokens (use the Tailwind name, not the hex)
| Group | Tailwind | Notes |
|---|---|---|
| Surfaces | `bg-canvas` `bg-surface` `bg-surface-2` | page / card / raised |
| Lines | `border-line` `border-line-strong` | strong >= 3:1, use for control borders |
| Text | `text-fg` `text-fg-2` `text-fg-muted` | ~17:1 / 12:1 / 8:1 on canvas |
| Accent | `bg-accent text-on-accent` `text-accent` `bg-accent-soft` | one calm gold accent |
| Focus | `--c-focus` (sky) | 3px ring on `:focus-visible`, global |
| Status | `text-danger bg-danger-bg border-danger-line`, same for `warn` `ok` `info` | with icon + word |
| Type | `text-xs 14` `sm 16` `base 18` `lg 20` `xl 24` `2xl 28` `3xl 34` `4xl 40` px | body = 18px; Devanagari line-height 1.85 |
| Radius | `rounded-ui-sm/md/lg/xl` | |
| Shadow | `shadow-flat` `shadow-overlay` | overlays only |
| Spacing | `--space-1..7`, `pb-tabbar` (= tab bar height) | |

Legacy classes (`btn-primary`, `btn-secondary`, `btn-ghost`, `btn-danger`, `input-field`, `section-card`, `glass-panel`,
`risk-badge-*`) still work and are now flat/48px. Old slate greys 400/500/600 were lifted to meet AA.

## Components (`src/components/ui`)
- `Button` `{variant: primary|secondary|ghost, size: lg|md, block, icon, loading}` + `ButtonLink` `{to,...}`.
- `UiCard` `{as, tone: default|raised|accent, padded}` (the older `components/Card.tsx` still exists for legacy pages).
- `BigTile` `{icon, label, to | onClick, speaker=true, speakText, onSpeak, hint}`: icon + word + speaker.
- `SpeakButton` `{text, label, onSpeak}`: 48px speaker; tap = listen, tap again = stop; hidden if speech unsupported.
- `SpeechNotice` `{show}`: "A Hindi voice is being used." etc. Render near any SpeakButton group.
- `RiskPill` `{level: high|medium|low, score, short}` (`components/RiskBadge.tsx` delegates to it).
- `Notice` `{tone: info|success|warn|error, title, onClose}`: icon + bold word + text; errors are `role="alert"`.
- `Spinner` `{size, label, visibleLabel}` (role=status), `Skeleton` `{className}`.
- `PageHeader` `{title, subtitle, icon, speaker, actions}`: the page `<h1>`; one per page.
- `FormField` `{label, hint, error, required, children(a11y)}`: ties label/hint/error with `id` and `aria-describedby`.
- `Modal` `{isOpen, onClose, title | labelledBy | ariaLabel, variant: dialog|sheet, size, closeOnBackdrop, hideClose}`:
  role=dialog, aria-modal, focus trap, Escape, initial focus, focus restore, scroll lock (`hooks/useDialogA11y.ts`).
- `Icon` `{name, size}`: inline SVG set (add paths in `Icon.tsx`).
- `LanguageSwitcher` `{variant: full|compact}`.

## Speech (`src/utils/speech.ts`, `src/hooks/useSpeech.ts`)
```ts
const { speak, stop, isSpeaking, speakingKey, isSupported, voicesReady, voice, notice } = useSpeech()
speak(text, { key?, lang?, onEnd? })   // strips markdown/emoji/URLs, chunks at sentence ends, speaks in the app language
voice   // { language: 'hi-IN', name, requested: 'mr-IN', match: 'exact' | 'fallback-hi' | 'fallback-en' } | null
notice  // null | 'unsupported' | 'noVoice' | 'hindiVoice' | 'englishVoice'  -> <SpeechNotice />
```
One shared controller app-wide (one voice at a time). Never throws when unsupported.

## Shell
`config/navigation.ts` defines `PRIMARY_NAV` (Home, Upload, Ask, Help = bottom tab bar on phones, top nav on desktop)
and `MORE_NAV` (the "More" sheet). Add secondary pages to `MORE_NAV`, not to the tab bar. Pages render inside
`<main id="main-content">`; the bottom bar reserves `--tabbar-h`, so no extra padding is needed.
