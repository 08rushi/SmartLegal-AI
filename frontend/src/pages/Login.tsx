export default function Login() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="card max-w-md w-full">
        <h1 className="text-2xl font-bold text-gray-900 mb-6 text-center">Sign in</h1>
        <div className="space-y-4">
          <input type="email" placeholder="Email" className="input-field" />
          <input type="password" placeholder="Password" className="input-field" />
          <button className="btn-primary w-full justify-center">Sign in</button>
        </div>
        <p className="text-center text-sm text-gray-500 mt-4">
          No account? <a href="/register" className="text-brand-500 font-medium">Register</a>
        </p>
      </div>
    </div>
  )
}
