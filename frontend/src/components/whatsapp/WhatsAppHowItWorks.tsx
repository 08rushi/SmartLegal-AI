const steps = [
  {
    number: '01',
    title: 'Open WhatsApp',
    description: 'Start a conversation with the SmartLegal-AI WhatsApp assistant.',
  },
  {
    number: '02',
    title: 'Ask or Send',
    description: 'Ask a legal question or send a supported agreement (PDF or Image).',
  },
  {
    number: '03',
    title: 'Get Legal Help',
    description: 'Receive clear, plain-language legal guidance and risk breakdown directly in chat.',
  },
]

export default function WhatsAppHowItWorks() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h2 className="text-2xl font-bold text-white tracking-tight">
          How it works
        </h2>
        <p className="text-sm text-slate-400">
          Get started in three simple steps.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {steps.map((step) => (
          <div
            key={step.number}
            className="relative rounded-2xl border border-slate-800/80 bg-slate-900/40 p-6 space-y-3"
          >
            <div className="text-3xl font-black text-amber-400/30">{step.number}</div>
            <h3 className="text-base font-bold text-white">{step.title}</h3>
            <p className="text-xs text-slate-400 leading-relaxed">{step.description}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
