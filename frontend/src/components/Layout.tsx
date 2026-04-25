import { Outlet, Link, useLocation } from 'react-router-dom'

export default function Layout() {
  const location = useLocation()

  return (
    <div className="min-h-screen flex flex-col">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-2xl">⚖️</span>
            <span className="font-bold text-gray-900 text-lg">SmartLegal AI</span>
          </Link>

          <div className="flex items-center gap-6">
            <Link
              to="/upload"
              className={`text-sm font-medium transition-colors ${
                location.pathname === '/upload'
                  ? 'text-brand-500'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Upload
            </Link>
            <Link
              to="/compare"
              className={`text-sm font-medium transition-colors ${
                location.pathname === '/compare'
                  ? 'text-brand-500'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Compare
            </Link>
            <Link to="/login" className="btn-secondary text-sm py-2 px-4">
              Sign in
            </Link>
            <Link to="/register" className="btn-primary text-sm py-2 px-4">
              Get started
            </Link>
          </div>
        </div>
      </nav>

      {/* Page content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-6 text-center text-sm text-gray-400">
        SmartLegal AI — Free legal document analysis for Indians 🇮🇳
      </footer>
    </div>
  )
}
