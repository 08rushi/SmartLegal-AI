import { Link } from 'react-router-dom'

export default function Register() {
  return (
    <div className="content-wrap py-8 sm:py-12">
      <div className="mx-auto grid max-w-6xl overflow-hidden rounded-[34px] border border-white/10 bg-[linear-gradient(180deg,rgba(15,22,38,0.94),rgba(11,18,31,0.92))] shadow-[0_30px_70px_rgba(0,0,0,0.35)] lg:grid-cols-[1.02fr_0.98fr]">
        <div className="p-6 sm:p-8 lg:p-10">
          <div className="mx-auto max-w-md">
            <p className="text-sm uppercase tracking-[0.26em] text-slate-500">Create Account</p>
            <h1 className="mt-4 text-3xl font-semibold text-white">Start your legal review workspace.</h1>
            <p className="mt-3 text-sm leading-7 text-slate-400">
              Create an account to save upload history, revisit analysis dashboards, and keep your question threads in one place.
            </p>

            <div className="mt-8 space-y-4">
              <div>
                <label className="mb-2 block text-sm text-slate-400">Full Name</label>
                <input type="text" placeholder="Enter your full name" className="input-field" />
              </div>
              <div>
                <label className="mb-2 block text-sm text-slate-400">Email Address</label>
                <input type="email" placeholder="Enter your email" className="input-field" />
              </div>
              <div>
                <label className="mb-2 block text-sm text-slate-400">Password</label>
                <input type="password" placeholder="Create a password" className="input-field" />
              </div>
              <button className="btn-primary w-full justify-center py-3.5">Create Account</button>
            </div>

            <p className="mt-5 text-sm text-slate-400">
              Already have an account?{' '}
              <Link to="/login" className="text-[#f5c26b] transition hover:text-white">
                Sign in
              </Link>
            </p>
          </div>
        </div>

        <div className="relative hidden min-h-[620px] overflow-hidden border-l border-white/10 lg:block">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom,rgba(245,194,107,0.16),transparent_35%),radial-gradient(circle_at_top,rgba(124,58,237,0.18),transparent_40%),linear-gradient(180deg,#0b1120,#090d17)]" />
          <div className="relative z-10 flex h-full flex-col justify-between p-10">
            <div>
              <p className="text-sm uppercase tracking-[0.26em] text-slate-500">Premium Access</p>
              <h2 className="mt-5 max-w-sm text-5xl font-semibold leading-tight text-white">Keep every insight, risk flag, and AI answer in one account.</h2>
            </div>
            <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6">
              <div className="grid gap-4">
                {['Saved document history', 'Persistent AI Q&A', 'Future comparison tools'].map((item) => (
                  <div key={item} className="rounded-[20px] border border-white/10 bg-white/[0.03] px-4 py-4 text-sm text-slate-300">
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
