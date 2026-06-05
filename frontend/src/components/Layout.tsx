import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { logout } from '../store/authSlice'
import { trackEvent } from '../utils/posthog'

const navItems = [
  { to: '/', label: 'Home' },
  { to: '/upload', label: 'Upload' },
  { to: '/analysis', label: 'Review' },
  { to: '/chat', label: 'Ask AI' },
  { to: '/compare', label: 'Knowledge Base' },
]

const serviceCards = [
  {
    key: 'legal-id',
    title: 'Legal ID Hub',
    icon: '🆔',
    description: 'Government ID guidance',
    to: '/legal-id'
  },
  {
    key: 'property',
    title: 'Property Hub',
    icon: '🏠',
    description: 'Property transactions',
    to: '/property-hub'
  },
  {
    key: 'business',
    title: 'Business License Hub',
    icon: '📊',
    description: 'Business registrations',
    to: '/business-hub'
  },
  {
    key: 'tracker',
    title: 'Service Tracker',
    icon: '4D',
    description: 'Checklists and reminders',
    to: '/tracker'
  },
  {
    key: 'all-services',
    title: 'View All Services',
    icon: '→',
    description: 'Complete service center',
    to: '/services'
  }
]

export default function Layout() {
  const location = useLocation()
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const { user, token } = useAppSelector((s) => s.auth)
  const [menuOpen, setMenuOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [servicesMenuOpen, setServicesMenuOpen] = useState(false)
  const servicesRef = useRef<HTMLDivElement>(null)
  const [isOffline, setIsOffline] = useState(() => (typeof navigator === 'undefined' ? false : !navigator.onLine))

  useEffect(() => {
    const handleOnline = () => setIsOffline(false)
    const handleOffline = () => setIsOffline(true)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  useEffect(() => {
    trackEvent('page_viewed', {
      path: location.pathname,
      search: location.search,
    })
  }, [location.pathname, location.search])

  const handleNavClick = () => {
    setMenuOpen(false)
    setUserMenuOpen(false)
  }
  const isAuthRoute = location.pathname === '/login' || location.pathname === '/register'

  function handleLogout() {
    dispatch(logout())
    setUserMenuOpen(false)
    navigate('/')
  }

  // Get user initials for avatar
  const initials = user?.name
    ? user.name.split(' ').map((n) => n[0]).slice(0, 2).join('').toUpperCase()
    : '?'

  return (
    <div className="page-shell min-h-screen bg-app">
      <div className="ambient-orb ambient-orb-left" />
      <div className="ambient-orb ambient-orb-right" />
      <div className="ambient-wave" />
      <div className="ambient-grid" />

      <header className="sticky top-0 z-50 px-3 pt-3 sm:px-5">
        <div className="content-wrap">
          <div className="glass-nav mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-5">

            {/* Logo */}
            <Link to="/" className="flex items-center gap-3" onClick={handleNavClick}>
              <span className="brand-mark">
                <span className="brand-mark__icon" aria-hidden="true">⚖</span>
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

            {/* Desktop nav */}
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

              {/* Services Dropdown */}
              <div className="relative" ref={servicesRef}>
                <button
                  type="button"
                  onClick={() => setServicesMenuOpen(!servicesMenuOpen)}
                  className={`rounded-full px-4 py-2 text-sm transition-all duration-200 flex items-center gap-1.5 ${
                    servicesMenuOpen || location.pathname.includes('/legal-id') || location.pathname.includes('/property') || location.pathname.includes('/business') || location.pathname === '/services' || location.pathname === '/tracker'
                      ? 'bg-white/10 text-[#f5c26b] shadow-[0_0_0_1px_rgba(245,194,107,0.15)]'
                      : 'text-slate-300 hover:bg-white/5 hover:text-white'
                  }`}
                >
                  Services
                  <span className={`transition-transform duration-200 ${servicesMenuOpen ? 'rotate-180' : ''}`}>▾</span>
                </button>

                {servicesMenuOpen && (
                  <div className="absolute top-full left-1/2 -translate-x-1/2 mt-3 w-96 rounded-2xl border border-white/15 bg-[#0f1626]/95 backdrop-blur-lg shadow-2xl overflow-hidden">
                    <div className="p-4 space-y-2">
                      {serviceCards.map((card) => (
                        <Link
                          key={card.key}
                          to={card.to}
                          onClick={() => setServicesMenuOpen(false)}
                          className="flex items-start gap-3 rounded-xl border border-white/10 bg-white/[0.03] p-3 transition-all hover:bg-white/[0.08] hover:border-white/15"
                        >
                          <span className="text-2xl pt-1">{card.icon}</span>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-white">{card.title}</p>
                            <p className="text-xs text-slate-400">{card.description}</p>
                          </div>
                          <span className="text-slate-400 mt-1">→</span>
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </nav>

            {/* Desktop auth area */}
            <div className="hidden items-center gap-3 lg:flex">
              {token && user ? (
                /* Logged-in user menu */
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setUserMenuOpen((v) => !v)}
                    className="flex items-center gap-2.5 rounded-2xl border border-white/15 bg-white/[0.04] px-3 py-2 text-sm text-slate-200 transition hover:border-[#f5c26b]/25"
                  >
                    <span className="flex h-7 w-7 items-center justify-center rounded-full border border-[#f5c26b]/25 bg-[#f5c26b]/15 text-xs font-semibold text-[#f5c26b]">
                      {initials}
                    </span>
                    <span className="max-w-[120px] truncate">{user.name.split(' ')[0]}</span>
                    <span className="text-slate-500">▾</span>
                  </button>

                  {userMenuOpen && (
                    <div className="absolute right-0 top-full mt-2 w-52 overflow-hidden rounded-2xl border border-white/15 bg-[#0f1626] shadow-2xl">
                      <div className="border-b border-white/10 px-4 py-3">
                        <p className="text-sm font-medium text-white truncate">{user.name}</p>
                        <p className="text-xs text-slate-500 truncate">{user.email}</p>
                      </div>
                      <div className="p-2">
                        <Link
                          to="/documents"
                          onClick={handleNavClick}
                          className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-slate-300 transition hover:bg-white/8 hover:text-white"
                        >
                          <span>📂</span> My Documents
                        </Link>
                        <Link
                          to="/tracker"
                          onClick={handleNavClick}
                          className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-slate-300 transition hover:bg-white/8 hover:text-white"
                        >
                          <span>4D</span> Service Tracker
                        </Link>
                        <Link
                          to="/upload"
                          onClick={handleNavClick}
                          className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-slate-300 transition hover:bg-white/8 hover:text-white"
                        >
                          <span>⬆</span> Upload Document
                        </Link>
                        <div className="my-1 border-t border-white/10" />
                        <button
                          type="button"
                          onClick={handleLogout}
                          className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-[#fb7185] transition hover:bg-[#fb7185]/10"
                        >
                          <span>↩</span> Sign Out
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                /* Logged-out CTA */
                <>
                  {!isAuthRoute && (
                    <Link to="/login" className="btn-secondary px-4 py-2.5">
                      Login
                    </Link>
                  )}
                  <Link to="/upload" className="btn-primary px-4 py-2.5">
                    Get Started
                  </Link>
                </>
              )}
            </div>

            {/* Mobile hamburger */}
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

          {/* Mobile menu */}
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
                        isActive ? 'bg-white/10 text-[#f5c26b]' : 'text-slate-300 hover:bg-white/5 hover:text-white'
                      }`
                    }
                  >
                    {item.label}
                  </NavLink>
                ))}

                {/* Mobile Services Submenu */}
                <div className="rounded-2xl border border-white/10 overflow-hidden">
                  <button
                    type="button"
                    onClick={() => setServicesMenuOpen(!servicesMenuOpen)}
                    className="w-full text-left rounded-2xl px-4 py-3 text-sm text-slate-300 hover:bg-white/5 transition flex items-center justify-between"
                  >
                    <span>Services</span>
                    <span className={`transition-transform ${servicesMenuOpen ? 'rotate-180' : ''}`}>▾</span>
                  </button>
                  {servicesMenuOpen && (
                    <div className="space-y-1 border-t border-white/10 p-2 bg-white/[0.02]">
                      {serviceCards.map((card) => (
                        <Link
                          key={card.key}
                          to={card.to}
                          onClick={handleNavClick}
                          className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-white/10 transition"
                        >
                          <span className="text-lg">{card.icon}</span>
                          <div className="flex-1">
                            <p className="font-medium">{card.title}</p>
                            <p className="text-xs text-slate-500">{card.description}</p>
                          </div>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>

                {token && user && (
                  <>
                    <Link to="/tracker" onClick={handleNavClick} className="rounded-2xl px-4 py-3 text-sm text-slate-300 hover:bg-white/5 hover:text-white transition">
                      4D Service Tracker
                    </Link>
                    <Link to="/documents" onClick={handleNavClick} className="rounded-2xl px-4 py-3 text-sm text-slate-300 hover:bg-white/5 hover:text-white transition">
                    📂 My Documents
                    </Link>
                  </>
                )}
              </nav>

              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                {token && user ? (
                  <>
                    <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-slate-400">
                      Signed in as <span className="text-white">{user.name.split(' ')[0]}</span>
                    </div>
                    <button
                      type="button"
                      onClick={handleLogout}
                      className="btn-secondary justify-center text-[#fb7185]"
                    >
                      Sign Out
                    </button>
                  </>
                ) : (
                  <>
                    {!isAuthRoute && (
                      <Link to="/login" onClick={handleNavClick} className="btn-secondary justify-center">
                        Login
                      </Link>
                    )}
                    <Link to="/upload" onClick={handleNavClick} className="btn-primary justify-center">
                      Get Started
                    </Link>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </header>

      <main className="relative z-10">
        {isOffline && (
          <div className="content-wrap pt-4">
            <div className="rounded-[22px] border border-[#f5c26b]/25 bg-[#20170d]/85 px-4 py-3 text-sm text-[#fef3c7]">
              You are offline. Uploads and AI analysis will resume once your connection returns.
            </div>
          </div>
        )}
        <Outlet />
      </main>

      <footer className="relative z-10 px-4 pb-8 pt-10 sm:px-6 sm:pt-14">
        <div className="content-wrap">
          <div className="glass-panel mx-auto grid max-w-7xl gap-8 rounded-[32px] px-6 py-8 sm:px-8 lg:grid-cols-[1.2fr_0.9fr_0.8fr]">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <span className="brand-mark">
                  <span className="brand-mark__icon" aria-hidden="true">⚖</span>
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
              <p className="mb-4 text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">Product</p>
              <div className="grid gap-3 text-sm text-slate-300">
                {navItems.map((item) => (
                  <Link key={item.to} to={item.to} className="transition hover:text-[#f5c26b]">
                    {item.label}
                  </Link>
                ))}
                <Link to="/legal-id" className="transition hover:text-[#f5c26b]">Legal ID Hub</Link>
                <Link to="/property-hub" className="transition hover:text-[#f5c26b]">Property Hub</Link>
                <Link to="/business-hub" className="transition hover:text-[#f5c26b]">Business License Hub</Link>
                <Link to="/tracker" className="transition hover:text-[#f5c26b]">Service Tracker</Link>
                <Link to="/documents" className="transition hover:text-[#f5c26b]">My Documents</Link>
              </div>
            </div>

            <div className="space-y-4">
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">Built For</p>
              <div className="grid gap-3">
                {['Rental agreements', 'Employment contracts', 'Loan documents', 'Freelance service agreements'].map((item) => (
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
