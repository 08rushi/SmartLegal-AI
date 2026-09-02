const capabilities = [
  {
    icon: '⚖️',
    title: 'Legal Questions',
    description: 'Ask everyday legal questions and receive plain-language guidance grounded in Indian legal frameworks.',
  },
  {
    icon: '📄',
    title: 'Document Analysis',
    description: 'Send supported legal documents (PDFs or images up to 10 MB) through WhatsApp for rapid contract analysis.',
  },
  {
    icon: '🚨',
    title: 'Legal Risk Understanding',
    description: 'Understand critical risk ratings, high-risk clauses, obligations, and suggested next steps.',
  },
  {
    icon: '✍️',
    title: 'Progressive Legal Drafting',
    description: 'Progressively provide requirements and key terms through guided chat to work toward a legal draft.',
  },
  {
    icon: '💬',
    title: 'Context Preservation',
    description: 'Seamlessly continue discussing active documents and legal contexts without restarting conversation workflows.',
  },
  {
    icon: '🌐',
    title: 'Multilingual Assistance',
    description: 'Get responses in English, Hindi (हिंदी), or Marathi (मराठी), and change your language setting anytime.',
  },
]

export default function WhatsAppCapabilities() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h2 className="text-2xl font-bold text-white tracking-tight">
          What can you do on WhatsApp?
        </h2>
        <p className="text-sm text-slate-400">
          SmartLegal-AI brings core legal assistance capabilities straight to your mobile chat.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {capabilities.map((item, index) => (
          <div
            key={index}
            className="rounded-2xl border border-slate-800/80 bg-slate-900/50 p-6 space-y-3 transition duration-200 hover:border-slate-700 hover:bg-slate-900/80"
          >
            <div className="text-2xl">{item.icon}</div>
            <h3 className="text-base font-bold text-slate-100">{item.title}</h3>
            <p className="text-xs text-slate-400 leading-relaxed">{item.description}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
