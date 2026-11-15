# i18n conventions

Languages: `en`, `hi`, `mr` (registered in `languages.ts`). Everything is bundled; nothing is fetched at runtime
(fonts come from `@fontsource/*` via `src/fonts.ts`).

## Files
- `locales/<lang>/<namespace>.json` - **one namespace per page/area** (`home`, `auth`, `upload`, ...).
- Files are auto-discovered with `import.meta.glob`. To add a namespace: create the same `<ns>.json` in
  **all** language folders. No registration edits. `npm test` (key-parity test) fails on missing/extra/empty keys
  or mismatched `{{placeholders}}`.
- Shared strings (buttons, "Loading...", etc.) live in `common`; do not duplicate them per page.

## Using it
```tsx
const { t } = useTranslation('upload')           // page namespace
t('title')                                       // upload:title
t('common:save')                                 // another namespace
```

## Key naming
- Nested, camelCase, grouped by UI area: `hero.title`, `form.email.label`, `form.email.placeholder`, `errors.required`.
- Name by meaning, not by English text (`cta.start`, not `getStartedNow`).
- Attributes too: `title`, `placeholder`, `aria-label`, `alt` all use `t(...)`.

## Rules
1. **No hardcoded user-visible strings** in JSX (text, `title`, `placeholder`, `aria-label`, `alt`, toast/error messages
   in slices). `npm test` prints a hardcoded-text report (`src/tests/hardcoded_text.test.mjs`); drive it to zero.
2. **Interpolation, never concatenation**: `t('greeting', { name })` with `"Hello {{name}}"`; word order differs per language.
3. **Plurals**: use i18next suffixes `key_one` / `key_other` and pass `{ count }`
   (`"files_one": "{{count}} file"`, `"files_other": "{{count}} files"`). Add every form each language needs.
4. Markup inside text: use `<Trans i18nKey="ns:key" components={{ b: <strong /> }} />`.
5. Dates/numbers: `Intl.DateTimeFormat(i18n.language)` / `toLocaleString(i18n.language)`, not hand formatting.
6. Hindi/Marathi values must be real Devanagari translations (brand names and example emails excepted).
7. Edit JSON files with Edit/Write tools as UTF-8; do not rewrite them with shell text cmdlets (corrupts Devanagari).

## Backend content
Every API request sends `X-Lang: <en|hi|mr>` (axios interceptor in `services/api.ts`). Use `getCurrentLang()` from
`services/api.ts` when you need the code explicitly, e.g. a body/query `lang` for endpoints that take one
(analysis summaries, chat, advisor). Backend-generated text is shown as returned; do not translate it client-side.
When the user switches language, refetch language-dependent data (depend on `i18n.language` in the effect).

## AI content translation (analysis)
For hi / mr the Analysis page calls `translateAnalysis` (`POST /analyze/{id}/translate`, cached per language in the store) and
renders that view everywhere (summary, clauses, lists, PDF). English uses the base analysis. Insight panels
(consequences / negotiation) refetch when the language changes (`consequencesLang` / `negotiationLang` in the store).
PDF export: English = jsPDF download; Hindi/Marathi = browser print of a Noto Sans Devanagari report (`utils/pdfReport.ts`).
Demo content lives in the `demo` namespace. The hardcoded-text scan is strict by default (`I18N_STRICT=0` to relax).
