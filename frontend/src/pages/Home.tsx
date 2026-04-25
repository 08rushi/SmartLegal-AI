export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4">
      <div className="text-center max-w-2xl">
        <div className="inline-flex items-center gap-2 bg-brand-50 text-brand-700 text-sm font-medium px-4 py-1.5 rounded-full border border-brand-100 mb-6">
          🇮🇳 Built for India
        </div>
        <h1 className="text-5xl font-bold text-gray-900 mb-4 leading-tight">
          Understand any legal<br />document in minutes
        </h1>
        <p className="text-xl text-gray-500 mb-8">
          Upload your rental agreement, employment contract, or loan document.
          Get plain-language explanations and risk warnings — free, in English and Hindi.
        </p>
        <a href="/upload" className="btn-primary text-lg px-8 py-3">
          Upload a Document →
        </a>
        <p className="mt-4 text-sm text-gray-400">No login required to try • 100% free</p>
      </div>

      <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl w-full">
        {[
          { icon: "📄", title: "Upload any contract", desc: "PDF or image of rental deed, job offer, loan paper" },
          { icon: "🔍", title: "AI reads every clause", desc: "Gemini AI extracts and explains each clause simply" },
          { icon: "⚠️", title: "Risk warnings in Hindi", desc: "One-sided clauses flagged in plain English and Hindi" },
        ].map((f) => (
          <div key={f.title} className="card text-center">
            <div className="text-3xl mb-3">{f.icon}</div>
            <h3 className="font-semibold text-gray-900 mb-1">{f.title}</h3>
            <p className="text-sm text-gray-500">{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
