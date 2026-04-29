import { Link } from 'react-router-dom'

export default function Login() {
  return (
    <div className="content-wrap py-8 sm:py-12">
      <div className="mx-auto grid max-w-6xl overflow-hidden rounded-[34px] border border-white/10 bg-[linear-gradient(180deg,rgba(15,22,38,0.94),rgba(11,18,31,0.92))] shadow-[0_30px_70px_rgba(0,0,0,0.35)] lg:grid-cols-[0.92fr_1.08fr]">
        <div className="relative hidden min-h-[620px] overflow-hidden border-r border-white/10 lg:block">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(124,58,237,0.22),transparent_40%),linear-gradient(180deg,#0a1020,#090d17)]" />
          <div className="relative z-10 flex h-full flex-col justify-between p-10">
            <div>
              <p className="text-sm uppercase tracking-[0.26em] text-slate-500">Welcome Back</p>
              <h1 className="mt-5 max-w-sm text-5xl font-semibold leading-tight text-white">Sign in to continue your analysis.</h1>
            </div>
            <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6">
              <div className="mx-auto flex h-52 w-52 items-center justify-center rounded-full border border-[#f5c26b]/18 bg-[radial-gradient(circle,rgba(245,194,107,0.12),transparent_65%)] text-7xl text-[#f5c26b]">
                ⚖
              </div>
            </div>
          </div>
        </div>

        <div className="p-6 sm:p-8 lg:p-10">
          <div className="mx-auto max-w-md">
            <p className="text-sm uppercase tracking-[0.26em] text-slate-500">Sign In</p>
            <h2 className="mt-4 text-3xl font-semibold text-white">Access your saved reviews.</h2>
            <p className="mt-3 text-sm leading-7 text-slate-400">
              Resume previous uploads, keep your chat history, and continue reviewing legal documents with the same premium workspace.
            </p>

            <div className="mt-8 space-y-4">
              <div>
                <label className="mb-2 block text-sm text-slate-400">Email Address</label>
                <input type="email" placeholder="Enter your email" className="input-field" />
              </div>
              <div>
                <label className="mb-2 block text-sm text-slate-400">Password</label>
                <input type="password" placeholder="Enter your password" className="input-field" />
              </div>
              <button className="btn-primary w-full justify-center py-3.5">Sign In</button>
            </div>

            <div className="mt-5 flex items-center justify-between gap-3 text-sm">
              <button type="button" className="text-slate-500 transition hover:text-[#f5c26b]">
                Forgot Password?
              </button>
              <Link to="/register" className="text-slate-400 transition hover:text-white">
                Create an account
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
