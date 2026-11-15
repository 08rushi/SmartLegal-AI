# Improvements Plan — easier for low-literacy users

Research basis: voice, icons and graphics let first-time non-literate users navigate unaided (Microsoft Research, IBM); reassurance matters in money/legal flows. Test each change with about 5 low-literacy users before wide release.

| ID | Pri | Change | Sub-tasks | Effort |
|---|---|---|---|---|
| UXI-1 | High | Language-first screen — merged into UXI-13 | see UXI-13 | — |
| UXI-13 | High | **App-wide language switcher: Marathi, Hindi, English** (button on Home; whole app changes language) | (a) add i18n library (e.g. react-i18next) and set `<html lang>`; (b) locale files `en`, `hi`, `mr` with namespaces per page; (c) `LanguageSwitcher` on Home showing 3 native-script options (मराठी, हिंदी, English), built on existing `components/ui/LanguageSelector.tsx`; (d) persist choice (localStorage, and user profile when logged in); (e) translate shared shell first: Layout, nav, Home, auth pages; (f) translate remaining pages in batches: upload, analysis, chat, advisor, hubs, yojana, my-documents, errors/toasts; (g) tie into analysis content: today only `plain_english`/`plain_hindi` exist, so Marathi needs a backward-compatible `plain_marathi` field or on-demand translation — Architect decides; update `types/index.ts`; (h) backend user-facing messages and WhatsApp strings follow the chosen language; (i) Devanagari-safe fonts and line heights; (j) tests: no missing keys across the three locales, switch persists across reload, key pages render in each language | L |
| UXI-2 | High | Simple home: 4–5 big tiles (Upload, Ask, Schemes, Help), each icon + word + speaker | replace marketing text and `4D`/`BIZ`; real icons; mobile bottom tab bar | M |
| UXI-3 | High | Guided "What do you need help with?" flow replacing three similar hubs | question-led routing to Legal ID / Property / Business | M |
| UXI-4 | High | Analysis page: verdict first | top: traffic-light verdict, 3 key risks, next steps (FEA-2); below: full clauses | M |
| UXI-5 | High | Simple view by default, "show details" toggle | applies to analysis, clauses, summary | S |
| UXI-6 | Med | Plain words + tap-to-explain legal terms | glossary data; tooltip with audio | M |
| UXI-7 | Med | One big next-step button per screen; remove `alert()` | inline toasts | S |
| UXI-8 | Med | Reassurance lines ("Nothing is submitted", "You can undo this") | add on upload, share, delete | S |
| UXI-9 | Med | Larger default text, high contrast, low-data mode | token update; image/size limits | M |
| UXI-10 | Med | Promote WhatsApp bot on home with voice-note input | link + QR; enable voice notes in bot | M |
| UXI-11 | Med | Accessibility | modal focus trap, Escape, labels, screen-reader pass | M |
| UXI-12 | Low | Flatter high-contrast visual style (replace heavy glass theme) | design tokens; apply per page | L |
