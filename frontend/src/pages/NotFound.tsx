import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="content-wrap py-6 sm:py-8">
      <div className="section-card mx-auto grid max-w-7xl items-center gap-8 rounded-[34px] p-6 sm:p-8 lg:grid-cols-[0.92fr_1.08fr]">
        <div className="space-y-5">
          <p className="text-7xl font-semibold tracking-[-0.06em] text-[#8a5cff] sm:text-8xl lg:text-[8rem]">404</p>
          <div>
            <h1 className="text-3xl font-semibold text-white sm:text-4xl">Page Not Found</h1>
            <p className="mt-3 max-w-xl text-sm leading-7 text-slate-400 sm:text-base">
              Looks like you took a wrong turn. Let’s get you back to the legal review experience.
            </p>
          </div>
          <Link to="/" className="btn-primary inline-flex px-6 py-3.5">
            Go to Homepage →
          </Link>
        </div>

        <div className="relative mx-auto flex h-[320px] w-full max-w-[520px] items-center justify-center sm:h-[420px]">
          <div className="absolute bottom-10 h-16 w-56 rounded-full bg-[#7c3aed]/22 blur-3xl" />
          <div className="relative flex h-52 w-52 items-center justify-center rounded-full border border-white/10 bg-[radial-gradient(circle,rgba(124,58,237,0.22),transparent_60%)] shadow-[0_0_50px_rgba(124,58,237,0.2)] sm:h-64 sm:w-64">
            <div className="text-8xl text-[#0f1626] drop-shadow-[0_0_32px_rgba(245,194,107,0.22)] sm:text-9xl">♞</div>
          </div>
        </div>
      </div>
    </div>
  )
}
