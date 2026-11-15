/**
 * Tailwind theme = design tokens, mapped onto the original dark-glass / gold palette. Values come from CSS
 * variables in src/index.css (:root) so there is one source of truth. Prefer these names (bg-canvas, bg-surface, text-fg, text-fg-muted, border-line,
 * bg-accent text-on-accent, text-danger ...) in new code. See src/components/ui/README.md.
 *
 * @type {import('tailwindcss').Config}
 */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: 'var(--c-canvas)',
        surface: { DEFAULT: 'var(--c-surface)', 2: 'var(--c-surface-2)' },
        line: { DEFAULT: 'var(--c-line)', strong: 'var(--c-line-strong)' },
        fg: { DEFAULT: 'var(--c-fg)', 2: 'var(--c-fg-2)', muted: 'var(--c-fg-muted)' },
        accent: { DEFAULT: 'var(--c-accent)', strong: 'var(--c-accent-strong)', soft: 'var(--c-accent-soft)' },
        'on-accent': 'var(--c-on-accent)',
        focus: 'var(--c-focus)',
        danger: { DEFAULT: 'var(--c-danger)', bg: 'var(--c-danger-bg)', line: 'var(--c-danger-line)' },
        warn: { DEFAULT: 'var(--c-warn)', bg: 'var(--c-warn-bg)', line: 'var(--c-warn-line)' },
        ok: { DEFAULT: 'var(--c-ok)', bg: 'var(--c-ok-bg)', line: 'var(--c-ok-line)' },
        info: { DEFAULT: 'var(--c-info)', bg: 'var(--c-info-bg)', line: 'var(--c-info-line)' },

        // Legacy (kept so existing pages still compile).
        brand: {
          50:  '#f0f4ff',
          100: '#dbe4ff',
          500: '#4361ee',
          600: '#3451d1',
          700: '#2541b2',
          900: '#0d1f6e',
        },
        risk: {
          low:    '#16a34a',
          medium: '#d97706',
          high:   '#dc2626',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Noto Sans Devanagari', 'Nirmala UI', 'system-ui', 'sans-serif'],
        display: ['Poppins', 'Inter', 'Noto Sans Devanagari', 'sans-serif'],
      },
      // Original type scale (Tailwind defaults, 16px base).
      minHeight: { touch: '0px' },
      minWidth: { touch: '0px' },
      borderRadius: {
        'ui-sm': 'var(--radius-sm)',
        'ui-md': 'var(--radius-md)',
        'ui-lg': 'var(--radius-lg)',
        'ui-xl': 'var(--radius-xl)',
      },
      boxShadow: {
        flat: 'var(--shadow-1)',
        overlay: 'var(--shadow-overlay)',
      },
      spacing: { tabbar: 'var(--tabbar-h)' },
    },
  },
  plugins: [],
}
