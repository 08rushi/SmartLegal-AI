import { useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'

const navItems = [
  { to: '/', label: 'Home' },
  { to: '/upload', label: 'Upload' },
  { to: '/analysis', label: 'Review' },
  { to: '/chat', label: 'Ask AI' },
  { to: '/compare', label: 'Knowledge Base' },
]

export default function Layout() {
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  const handleNavClick = () => setMenuOpen(false)
  const isAuthRoute = location.pathname === '/login' || location.pathname === '/register'

  return (
    <div className="page-shell min-h-screen bg-app">
      <div className="ambient-orb ambient-orb-left" />
      <div className="ambient-orb ambient-orb-right" />
      <div className="ambient-wave" />
      <div className="ambient-grid" />

      <header className="sticky top-0 z-50 px-3 pt-3 sm:px-5">
        <div className="content-wrap">
          <div className="glass-nav mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-5">
            <Link to="/" className="flex items-center gap-3" onClick={handleNavClick}>
              <span className="brand-mark">
                <span className="brand-mark__icon" aria-hidden="true">
                  ⚖
                </span>
              </span>
              <div>
                <p className="text-[10px] uppercase tracking-[0.32em] text-slate-500 sm:text-[11px]">
                  Legal Intelligence
                </p>
                <p className="font-['Poppins'] text-base font-semibold text-[#f5c26b] sm:text-lg">
                  SmartLegal AI
                </p>
              </div>
            </Link>

            <nav className="hidden items-center gap-2 lg:flex">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `rounded-full px-4 py-2 text-sm transition-all duration-200 ${
                      isActive
                        ? 'bg-white/10 text-[#f5c26b] shadow-[0_0_0_1px_rgba(245,194,107,0.15)]'
                        : 'text-slate-300 hover:bg-white/5 hover:text-white'
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>

            <div className="hidden items-center gap-3 lg:flex">
              {!isAuthRoute && (
                <Link to="/login" className="btn-secondary px-4 py-2.5">
                  Login
                </Link>
              )}
              <Link to="/upload" className="btn-primary px-4 py-2.5">
                Get Started
              </Link>
            </div>

            <button
              type="button"
              aria-label="Toggle navigation menu"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((open) => !open)}
              className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/5 text-slate-200 transition hover:border-[#f5c26b]/30 hover:text-white lg:hidden"
            >
              <span className="space-y-1.5">
                <span className="block h-0.5 w-5 rounded-full bg-current" />
                <span className="block h-0.5 w-5 rounded-full bg-current" />
                <span className="block h-0.5 w-5 rounded-full bg-current" />
              </span>
            </button>
          </div>

          {menuOpen && (
            <div className="glass-panel mx-auto mt-3 max-w-7xl rounded-[26px] p-3 lg:hidden">
              <nav className="flex flex-col gap-2">
                {navItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={handleNavClick}
                    className={({ isActive }) =>
                      `rounded-2xl px-4 py-3 text-sm transition ${
                        isActive
                          ? 'bg-white/10 text-[#f5c26b]'
                          : 'text-slate-300 hover:bg-white/5 hover:text-white'
                      }`
                    }
                  >
                    {item.label}
                  </NavLink>
                ))}
              </nav>

              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                {!isAuthRoute && (
                  <Link to="/login" onClick={handleNavClick} className="btn-secondary justify-center">
                    Login
                  </Link>
                )}
                <Link to="/upload" onClick={handleNavClick} className="btn-primary justify-center">
                  Get Started
                </Link>
              </div>
            </div>
          )}
        </div>
      </header>

      <main className="relative z-10">
        <Outlet />
      </main>

      <footer className="relative z-10 px-4 pb-8 pt-10 sm:px-6 sm:pt-14">
        <div className="content-wrap">
          <div className="glass-panel mx-auto grid max-w-7xl gap-8 rounded-[32px] px-6 py-8 sm:px-8 lg:grid-cols-[1.2fr_0.9fr_0.8fr]">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <span className="brand-mark">
                  <span className="brand-mark__icon" aria-hidden="true">
                    ⚖
                  </span>
                </span>
                <div>
                  <p className="font-['Poppins'] text-lg font-semibold text-[#f5c26b]">SmartLegal AI</p>
                  <p className="text-sm text-slate-400">Plain-language legal guidance for Indian users.</p>
                </div>
              </div>
              <p className="max-w-xl text-sm leading-7 text-slate-400">
                Upload agreements, review risk warnings, and ask follow-up questions in one premium workspace built for real document decisions.
              </p>
              <div className="flex flex-wrap gap-3 text-xs uppercase tracking-[0.24em] text-slate-500">
                <span>Smooth workflow</span>
                <span>Dark premium UI</span>
                <span>Hindi + English</span>
              </div>
            </div>

            <div>
              <p className="mb-4 text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
                Product
              </p>
              <div className="grid gap-3 text-sm text-slate-300">
                {navItems.map((item) => (
                  <Link key={item.to} to={item.to} className="transition hover:text-[#f5c26b]">
                    {item.label}
                  </Link>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
                Built For
              </p>
              <div className="grid gap-3">
                {[
                  'Rental agreements',
                  'Employment contracts',
                  'Loan documents',
                  'Freelance service agreements',
                ].map((item) => (
                  <div key={item} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-slate-300">
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
