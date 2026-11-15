import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { logout, logoutAllSessions } from '../store/authSlice'
import { trackEvent } from '../utils/posthog'
import CategoryArt from './CategoryArt'
import GlobalFloatingActions from './GlobalFloatingActions'
import { LanguageSwitcher } from './ui/LanguageSwitcher'
import { FOOTER_EXTRA_LINKS, NAV_ITEMS, SERVICE_CARDS, isServicesActive } from '../config/navigation'

export default function Layout() {
  const { t } = useTranslation()
  const location = useLocation()
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const { user, isAuthenticated } = useAppSelector((s) => s.auth)
  const [menuOpen, setMenuOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [servicesMenuOpen, setServicesMenuOpen] = useState(false)
  const servicesRef = useRef<HTMLDivElement>(null)
  const mobileServicesRef = useRef<HTMLDivElement>(null)
  const userMenuRef = useRef<HTMLDivElement>(null)
  const mainRef = useRef<HTMLElement>(null)
  const firstRender = useRef(true)
  const [isOffline, setIsOffline] = useState(() => (typeof navigator === 'undefined' ? false : !navigator.onLine))

  // Close the Services dropdown when clicking anywhere outside it.
  useEffect(() => {
    if (!servicesMenuOpen) return
    const handlePointerDown = (e: MouseEvent | TouchEvent) => {
      const target = e.target as Node
      const inDesktop = servicesRef.current?.contains(target)
      const inMobile = mobileServicesRef.current?.contains(target)
      if (!inDesktop && !inMobile) setServicesMenuOpen(false)
    }
    document.addEventListener('mousedown', handlePointerDown)
    document.addEventListener('touchstart', handlePointerDown)
    return () => {
      document.removeEventListener('mousedown', handlePointerDown)
      document.removeEventListener('touchstart', handlePointerDown)
    }
  }, [servicesMenuOpen])

  // Close the user menu on an outside click; Escape closes any open menu.
  useEffect(() => {
    if (!userMenuOpen && !servicesMenuOpen && !menuOpen) return
    const handlePointerDown = (e: MouseEvent | TouchEvent) => {
      if (userMenuOpen && !userMenuRef.current?.contains(e.target as Node)) setUserMenuOpen(false)
    }
    const handleKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return
      setUserMenuOpen(false)
      setServicesMenuOpen(false)
      setMenuOpen(false)
    }
    document.addEventListener('mousedown', handlePointerDown)
    document.addEventListener('touchstart', handlePointerDown)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('mousedown', handlePointerDown)
      document.removeEventListener('touchstart', handlePointerDown)
      document.removeEventListener('keydown', handleKey)
    }
  }, [userMenuOpen, servicesMenuOpen, menuOpen])

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
    window.scrollTo(0, 0)
    // Move keyboard / screen-reader focus to the page content after navigating (not on first load).
    if (firstRender.current) firstRender.current = false
    else mainRef.current?.focus({ preventScroll: true })
    setMenuOpen(false)
    setUserMenuOpen(false)
    setServicesMenuOpen(false)
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

  async function handleLogoutAll() {
    setUserMenuOpen(false)
    try {
      await dispatch(logoutAllSessions()).unwrap()
    } catch {
      dispatch(logout()) // fall back to local sign-out if the call fails
    }
    navigate('/login')
  }

  // Get user initials for avatar
  const initials = user?.name
    ? user.name.split(' ').map((n) => n[0]).slice(0, 2).join('').toUpperCase()
    : '?'

  return (
    <div className="page-shell min-h-screen bg-app">
      <div className="ambient-orb ambient-orb-left" aria-hidden="true" />
      <div className="ambient-orb ambient-orb-right" aria-hidden="true" />
      <div className="ambient-wave" aria-hidden="true" />
      <div className="ambient-grid" aria-hidden="true" />

      <a href="#main-content" className="skip-link">
        {t('nav:skipToContent')}
      </a>

      <header className="sticky top-0 z-50 px-4 pt-3 sm:px-6 lg:px-8">
        <div className="glass-nav mx-auto flex w-full max-w-[1440px] flex-nowrap items-center justify-between gap-3 px-4 py-2.5 sm:px-6 sm:py-3">

            {/* Logo */}
            <Link to="/" aria-label={t('nav:homeLink')} className="flex shrink-0 items-center gap-3" onClick={handleNavClick}>
              <span className="brand-mark">
                <span className="brand-mark__icon" aria-hidden="true">⚖</span>
              </span>
              <div className="leading-tight">
                <p className="hidden whitespace-nowrap text-[10px] uppercase tracking-[0.24em] text-slate-500 min-[1700px]:block">
                  {t('nav:brandTagline')}
                </p>
                <p className="whitespace-nowrap font-['Poppins'] text-base font-semibold text-[#f5c26b] sm:text-lg">
                  SmartLegal AI
                </p>
              </div>
            </Link>

            {/* Desktop nav */}
            <nav aria-label={t('nav:mainMenu')} className="hidden min-w-0 flex-1 items-center justify-center gap-0.5 min-[1200px]:flex">
              {NAV_ITEMS.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    `inline-flex h-10 items-center whitespace-nowrap rounded-full px-2.5 text-sm font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-white/10 text-[#f5c26b] shadow-[0_0_0_1px_rgba(245,194,107,0.15)]'
                        : 'text-slate-300 hover:bg-white/5 hover:text-white'
                    }`
                  }
                >
                  {t(item.labelKey)}
                </NavLink>
              ))}

              {/* Services Dropdown */}
              <div className="relative" ref={servicesRef}>
                <button
                  type="button"
                  onClick={() => setServicesMenuOpen(!servicesMenuOpen)}
                  aria-expanded={servicesMenuOpen}
                  aria-haspopup="true"
                  className={`inline-flex h-10 items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 text-sm font-medium transition-all duration-200 ${
                    servicesMenuOpen || isServicesActive(location.pathname)
                      ? 'bg-white/10 text-[#f5c26b] shadow-[0_0_0_1px_rgba(245,194,107,0.15)]'
                      : 'text-slate-300 hover:bg-white/5 hover:text-white'
                  }`}
                >
                  {t('nav:services')}
                  <span aria-hidden="true" className={`transition-transform duration-200 ${servicesMenuOpen ? 'rotate-180' : ''}`}>▾</span>
                </button>

                {servicesMenuOpen && (
                  <div className="absolute top-full left-1/2 -translate-x-1/2 mt-3 w-96 rounded-2xl border border-white/15 bg-[#0f1626]/95 backdrop-blur-lg shadow-2xl overflow-hidden">
                    <div className="p-4 space-y-2">
                      {SERVICE_CARDS.map((card) => (
                        <Link
                          key={card.key}
                          to={card.to}
                          onClick={() => setServicesMenuOpen(false)}
                          className="group flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.03] p-2.5 transition-all hover:bg-white/[0.08] hover:border-white/15"
                        >
                          <span className="block h-11 w-[52px] shrink-0 overflow-hidden rounded-lg border border-white/10" aria-hidden="true">
                            <CategoryArt art={card.art} className="block h-full w-full" />
                          </span>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-white">{t(card.titleKey)}</p>
                            <p className="text-xs text-slate-400">{t(card.descriptionKey)}</p>
                          </div>
                          <span aria-hidden="true" className="text-slate-400 transition-transform group-hover:translate-x-0.5">→</span>
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Legal Advisor — highlighted */}
              <NavLink
                to="/advisor"
                className={({ isActive }) =>
                  `ml-1 inline-flex h-10 items-center gap-2 whitespace-nowrap rounded-full border px-2.5 text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'border-[#f5c26b]/40 bg-[#f5c26b]/15 text-[#f5c26b]'
                      : 'border-[#f5c26b]/25 bg-[#f5c26b]/8 text-[#f5c26b] hover:bg-[#f5c26b]/15'
                  }`
                }
              >
                <span aria-hidden="true" className="text-base leading-none">⚖️</span>
                {t('nav:legalAdvisor')}
              </NavLink>
            </nav>

            <div className="flex shrink-0 items-center gap-2 sm:gap-3">
              {/* Language selector (phones get it inside the mobile menu) */}
              <div className="hidden sm:block">
                <LanguageSwitcher variant="compact" />
              </div>

              {/* Desktop auth area */}
              <div className="hidden items-center gap-3 min-[1200px]:flex">
                {isAuthenticated && user ? (
                  /* Logged-in user menu */
                  <div className="relative" ref={userMenuRef}>
                    <button
                      type="button"
                      onClick={() => setUserMenuOpen((v) => !v)}
                      aria-expanded={userMenuOpen}
                      aria-haspopup="true"
                      aria-label={t('shell:userMenu')}
                      className="flex h-11 items-center gap-2.5 whitespace-nowrap rounded-2xl border border-white/15 bg-white/[0.04] px-3 text-sm text-slate-200 transition hover:border-[#f5c26b]/25"
                    >
                      <span className="flex h-7 w-7 items-center justify-center rounded-full border border-[#f5c26b]/25 bg-[#f5c26b]/15 text-xs font-semibold text-[#f5c26b]">
                        {initials}
                      </span>
                      <span className="hidden max-w-[120px] truncate min-[1500px]:inline">{user.name.split(' ')[0]}</span>
                      <span className="text-slate-500" aria-hidden="true">▾</span>
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
                            <span aria-hidden="true">📂</span> {t('nav:myDocuments')}
                          </Link>
                          <Link
                            to="/tracker"
                            onClick={handleNavClick}
                            className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-slate-300 transition hover:bg-white/8 hover:text-white"
                          >
                            <span aria-hidden="true">📋</span> {t('nav:serviceTracker')}
                          </Link>
                          <Link
                            to="/upload"
                            onClick={handleNavClick}
                            className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-slate-300 transition hover:bg-white/8 hover:text-white"
                          >
                            <span aria-hidden="true">⬆</span> {t('nav:uploadDocument')}
                          </Link>
                          <div className="my-1 border-t border-white/10" />
                          <button
                            type="button"
                            onClick={handleLogout}
                            className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-[#fb7185] transition hover:bg-[#fb7185]/10"
                          >
                            <span aria-hidden="true">↩</span> {t('nav:signOut')}
                          </button>
                          <button
                            type="button"
                            onClick={handleLogoutAll}
                            className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-slate-400 transition hover:bg-white/8 hover:text-white"
                          >
                            <span aria-hidden="true">⇥</span> {t('nav:signOutEverywhere')}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  /* Logged-out CTA */
                  <>
                    {!isAuthRoute && (
                      <Link to="/login" className="btn-secondary inline-flex h-11 items-center whitespace-nowrap px-4 py-0">
                        {t('nav:login')}
                      </Link>
                    )}
                    <Link to="/upload" className="btn-primary inline-flex h-11 items-center whitespace-nowrap px-4 py-0">
                      {t('nav:getStarted')}
                    </Link>
                  </>
                )}
              </div>

              {/* Mobile hamburger */}
              <button
                type="button"
                aria-label={t('nav:toggleMenu')}
                aria-expanded={menuOpen}
                aria-controls="mobile-menu"
                onClick={() => setMenuOpen((open) => !open)}
                className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/5 text-slate-200 transition hover:border-[#f5c26b]/30 hover:text-white min-[1200px]:hidden"
              >
                <span className="space-y-1.5" aria-hidden="true">
                  <span className="block h-0.5 w-5 rounded-full bg-current" />
                  <span className="block h-0.5 w-5 rounded-full bg-current" />
                  <span className="block h-0.5 w-5 rounded-full bg-current" />
                </span>
              </button>
            </div>
          </div>

          {/* Mobile menu */}
          {menuOpen && (
            <div id="mobile-menu" className="glass-panel mx-auto mt-3 max-w-[1440px] rounded-[26px] p-3 min-[1200px]:hidden">
              <div className="mb-2 sm:hidden">
                <LanguageSwitcher variant="compact" />
              </div>
              <nav aria-label={t('nav:mainMenu')} className="flex flex-col gap-2">
                {NAV_ITEMS.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === '/'}
                    onClick={handleNavClick}
                    className={({ isActive }) =>
                      `rounded-2xl px-4 py-3 text-sm transition ${
                        isActive ? 'bg-white/10 text-[#f5c26b]' : 'text-slate-300 hover:bg-white/5 hover:text-white'
                      }`
                    }
                  >
                    {t(item.labelKey)}
                  </NavLink>
                ))}

                {/* Mobile Services Submenu */}
                <div className="rounded-2xl border border-white/10 overflow-hidden" ref={mobileServicesRef}>
                  <button
                    type="button"
                    onClick={() => setServicesMenuOpen(!servicesMenuOpen)}
                    aria-expanded={servicesMenuOpen}
                    className="w-full text-left rounded-2xl px-4 py-3 text-sm text-slate-300 hover:bg-white/5 transition flex items-center justify-between"
                  >
                    <span>{t('nav:services')}</span>
                    <span aria-hidden="true" className={`transition-transform ${servicesMenuOpen ? 'rotate-180' : ''}`}>▾</span>
                  </button>
                  {servicesMenuOpen && (
                    <div className="space-y-1 border-t border-white/10 p-2 bg-white/[0.02]">
                      {SERVICE_CARDS.map((card) => (
                        <Link
                          key={card.key}
                          to={card.to}
                          onClick={handleNavClick}
                          className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-white/10 transition"
                        >
                          <span className="block h-9 w-[42px] shrink-0 overflow-hidden rounded-md border border-white/10" aria-hidden="true">
                            <CategoryArt art={card.art} className="block h-full w-full" />
                          </span>
                          <div className="flex-1">
                            <p className="font-medium">{t(card.titleKey)}</p>
                            <p className="text-xs text-slate-500">{t(card.descriptionKey)}</p>
                          </div>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>

                <NavLink
                  to="/advisor"
                  onClick={handleNavClick}
                  className={({ isActive }) =>
                    `rounded-2xl px-4 py-3 text-sm font-medium transition ${
                      isActive ? 'bg-[#f5c26b]/15 text-[#f5c26b]' : 'border border-[#f5c26b]/25 bg-[#f5c26b]/8 text-[#f5c26b] hover:bg-[#f5c26b]/15'
                    }`
                  }
                >
                  <span className="inline-flex items-center gap-2"><span aria-hidden="true" className="text-base leading-none">⚖️</span> {t('nav:legalAdvisor')}</span>
                </NavLink>

                {isAuthenticated && user && (
                  <>
                    <Link to="/tracker" onClick={handleNavClick} className="rounded-2xl px-4 py-3 text-sm text-slate-300 hover:bg-white/5 hover:text-white transition">
                      <span aria-hidden="true">📋</span> {t('nav:serviceTracker')}
                    </Link>
                    <Link to="/documents" onClick={handleNavClick} className="rounded-2xl px-4 py-3 text-sm text-slate-300 hover:bg-white/5 hover:text-white transition">
                      <span aria-hidden="true">📂</span> {t('nav:myDocuments')}
                    </Link>
                  </>
                )}
              </nav>

              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                {isAuthenticated && user ? (
                  <>
                    <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-slate-400">
                      {t('nav:signedInAs', { name: user.name.split(' ')[0] })}
                    </div>
                    <button
                      type="button"
                      onClick={handleLogout}
                      className="btn-secondary justify-center text-[#fb7185]"
                    >
                      {t('nav:signOut')}
                    </button>
                    <button
                      type="button"
                      onClick={handleLogoutAll}
                      className="btn-secondary justify-center sm:col-span-2"
                    >
                      {t('nav:signOutEverywhere')}
                    </button>
                  </>
                ) : (
                  <>
                    {!isAuthRoute && (
                      <Link to="/login" onClick={handleNavClick} className="btn-secondary justify-center">
                        {t('nav:login')}
                      </Link>
                    )}
                    <Link to="/upload" onClick={handleNavClick} className="btn-primary justify-center">
                      {t('nav:getStarted')}
                    </Link>
                  </>
                )}
              </div>
            </div>
          )}
      </header>

      <main id="main-content" ref={mainRef} tabIndex={-1} className="relative z-10 outline-none">
        {isOffline && (
          <div className="content-wrap pt-4">
            <div role="status" className="rounded-[22px] border border-[#f5c26b]/25 bg-[#20170d]/85 px-4 py-3 text-sm text-[#fef3c7]">
              {t('nav:offline')}
            </div>
          </div>
        )}
        <Outlet />
      </main>

      <footer className="relative z-10 px-4 pb-8 pt-10 sm:px-6 sm:pt-6">
        <div className="content-wrap">
          <div className="glass-panel mx-auto grid max-w-7xl gap-8 rounded-[32px] px-6 py-8 sm:px-8 lg:grid-cols-[1.2fr_0.9fr_0.8fr]">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <span className="brand-mark">
                  <span className="brand-mark__icon" aria-hidden="true">⚖</span>
                </span>
                <div>
                  <p className="font-['Poppins'] text-lg font-semibold text-[#f5c26b]">SmartLegal AI</p>
                  <p className="text-sm text-slate-400">{t('footer:tagline')}</p>
                </div>
              </div>
              <p className="max-w-xl text-sm leading-7 text-slate-400">{t('footer:intro')}</p>
              <div className="flex flex-wrap gap-3 text-xs uppercase tracking-[0.24em] text-slate-500">
                <span>{t('footer:tags.law')}</span>
                <span>{t('footer:tags.types')}</span>
                <span>{t('footer:tags.languages')}</span>
              </div>
            </div>

            <div>
              <p className="mb-4 text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">{t('footer:product')}</p>
              <nav aria-label={t('footer:product')} className="grid gap-3 text-sm text-slate-300">
                {[...NAV_ITEMS, ...FOOTER_EXTRA_LINKS].map((item) => (
                  <Link key={item.to} to={item.to} className="transition hover:text-[#f5c26b]">
                    {t(item.labelKey)}
                  </Link>
                ))}
              </nav>
            </div>

            <div className="space-y-4">
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">{t('footer:analyzes')}</p>
              <div className="grid gap-3">
                {['rental', 'employment', 'court', 'family', 'cheque', 'wills'].map((k) => (
                  <div key={k} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-slate-300">
                    {t(`footer:items.${k}`)}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Disclaimer + copyright bar */}
          <div className="mx-auto mt-4 flex max-w-7xl flex-col gap-3 px-2 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
            <p>{t('footer:copyright', { year: new Date().getFullYear() })}</p>
            <p className="sm:text-right">{t('footer:disclaimer')}</p>
          </div>
        </div>
      </footer>

      {/* Global Floating Action System */}
      <GlobalFloatingActions />
    </div>
  )
}
