import { useEffect, useRef, useState } from 'react'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { addAdvisorUserMessage, clearAdvisor, sendAdvisorMessage } from '../store/advisorSlice'
import { trackEvent } from '../utils/posthog'
import { Card } from '../components/Card'
import AdvocateIcon from '../components/AdvocateIcon'
import MarkdownMessage from '../components/MarkdownMessage'

const starterPrompts = [
  "I'm about to sign a rental agreement — which clauses protect me and what should I avoid?",
  'I want to file a case against someone who did not repay my loan. What are my options and chances?',
  'Which Constitution Articles and Acts apply to my property dispute with a neighbour?',
  'A cheque given to me bounced — how do I recover the money and can the person be prosecuted?',
  'My employer terminated me without notice. What can I do and under which law?',
  'I am starting a business partnership — what terms must the deed include to protect me?',
]

export default function Advisor() {
  const dispatch = useAppDispatch()
  const { messages, isLoading, error } = useAppSelector((s) => s.advisor)
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = async (question?: string) => {
    const text = (question ?? input).trim()
    if (!text || isLoading) return
    setInput('')
    dispatch(addAdvisorUserMessage(text))
    trackEvent('advisor_question_sent', { questionLength: text.length })
    await dispatch(sendAdvisorMessage(text))
  }

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="content-wrap min-h-screen px-3 py-3 sm:px-4 sm:py-4 lg:px-6 lg:py-5">
      <div className="mx-auto grid max-w-7xl gap-4 xl:grid-cols-[280px_minmax(0,1fr)]">
        {/* Sidebar */}
        <Card as="aside" variant="section" className="hidden h-fit rounded-[24px] p-5 xl:block">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-[#f5c26b]/25 bg-[#f5c26b]/10 text-[#f5c26b]">
            <AdvocateIcon className="h-6 w-6" />
          </div>
          <h1 className="mt-4 text-2xl font-semibold text-white">AI Legal Advisor</h1>
          <p className="mt-3 text-sm leading-7 text-slate-400">
            Consult a virtual Indian advocate. Describe your situation — a contract you are about to sign, a
            dispute, or a case you want to file — and get advice grounded in the Constitution, Acts and sections.
          </p>

          <div className="mt-6 space-y-2 text-sm text-slate-300">
            {[
              'Contracts — safe terms & red flags',
              'Cases — applicable Articles & Acts',
              'Realistic chances & strategy',
              'Concrete next steps',
            ].map((item) => (
              <div key={item} className="flex items-start gap-2">
                <span className="mt-0.5 text-[#34d399]">✓</span>
                <span>{item}</span>
              </div>
            ))}
          </div>

          {messages.length > 0 && (
            <button
              type="button"
              onClick={() => dispatch(clearAdvisor())}
              className="btn-secondary mt-6 w-full justify-center"
            >
              New Consultation
            </button>
          )}
        </Card>

        {/* Consultation Section */}
        <Card
          as="section"
          variant="section"
          className="flex min-h-[calc(100vh-24px)] min-w-0 flex-col overflow-hidden rounded-[24px] p-3 sm:min-h-[calc(100vh-32px)] sm:rounded-[30px] sm:p-4 md:p-5 lg:min-h-[calc(100vh-40px)] lg:p-6"
        >
          {/* Header */}
          <div className="shrink-0 border-b border-white/8 pb-3 sm:pb-4">
            <p className="text-xs text-slate-500 sm:text-sm">Virtual Indian Advocate</p>
            <div className="mt-1 flex items-center justify-between gap-3">
              <h2 className="text-xl font-semibold text-white sm:text-2xl lg:text-3xl">Ask a AI Lawyer Anything</h2>
              <div className="flex items-center gap-2">
                {messages.length > 0 && (
                  <button
                    type="button"
                    onClick={() => dispatch(clearAdvisor())}
                    className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs text-slate-300 transition hover:border-white/25 hover:text-white xl:hidden"
                  >
                    New
                  </button>
                )}
                <span className="hidden shrink-0 rounded-full border border-[#f5c26b]/20 bg-[#f5c26b]/10 px-3 py-1 text-xs text-[#f5c26b] sm:block">
                  Indian Law
                </span>
              </div>
            </div>
            <p className="mt-1 max-w-3xl text-xs leading-5 text-slate-400 sm:mt-2 sm:text-sm sm:leading-6">
              Advice on contracts, disputes, court cases, your rights, and strategy — grounded in Indian law and Acts.
            </p>
          </div>

          {/* Content */}
          <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col justify-center py-4 sm:py-5">
            {messages.length === 0 ? (
              <div className="space-y-5 text-center">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-[18px] border border-[#f5c26b]/25 bg-[#f5c26b]/10 text-[#f5c26b] sm:h-16 sm:w-16">
                  <AdvocateIcon className="h-7 w-7 sm:h-8 sm:w-8" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white sm:text-xl">How can I help with your legal matter?</h3>
                  <p className="mx-auto mt-1 max-w-xl text-xs leading-5 text-slate-400 sm:text-sm">
                    Describe your situation in your own words. Try one of these to start:
                  </p>
                </div>
                <div className="mx-auto grid max-w-2xl gap-2 sm:grid-cols-2">
                  {starterPrompts.map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      onClick={() => handleSend(prompt)}
                      className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-left text-xs leading-5 text-slate-300 transition hover:border-[#f5c26b]/30 hover:text-white sm:text-sm"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-3 sm:space-y-4">
                {messages.map((msg) => (
                  <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div
                      className={`max-w-[92%] rounded-[18px] px-3 py-2.5 text-xs leading-5 sm:max-w-[82%] sm:rounded-[22px] sm:px-4 sm:py-3 sm:text-sm sm:leading-6 ${
                        msg.role === 'user'
                          ? 'bg-[linear-gradient(180deg,#f5c26b,#cf9b42)] text-slate-950 shadow-[0_12px_25px_rgba(245,194,107,0.18)]'
                          : 'border border-white/10 bg-white/[0.03] text-slate-200'
                      }`}
                    >
                      {msg.role === 'assistant' && (
                        <p className="mb-1 text-[9px] uppercase tracking-[0.2em] text-slate-500 sm:text-[10px]">
                          SmartLegal AI Advisor
                        </p>
                      )}
                      {msg.role === 'assistant' ? (
                        <MarkdownMessage content={msg.content} />
                      ) : (
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      )}
                      <p className={`mt-1 text-[9px] ${msg.role === 'user' ? 'text-slate-800/60' : 'text-slate-500'}`}>
                        {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                ))}

                {isLoading && (
                  <div className="flex justify-start">
                    <div className="rounded-[18px] border border-white/10 bg-white/[0.03] px-3 py-2.5">
                      <div className="flex items-center gap-2">
                        <span className="text-[9px] uppercase tracking-[0.2em] text-slate-500">Reviewing your matter</span>
                        {[0, 1, 2].map((dot) => (
                          <span
                            key={dot}
                            className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#f5c26b]"
                            style={{ animationDelay: `${dot * 0.15}s` }}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {error && (
                  <div className="rounded-[18px] border border-[#fb7185]/25 bg-[#2a1320]/65 px-3 py-2.5 text-xs text-[#fecdd3] sm:text-sm">
                    {error}
                  </div>
                )}

                <div ref={bottomRef} />
              </div>
            )}
          </div>

          {/* Input */}
          <div className="mx-auto w-full max-w-4xl shrink-0 border-t border-white/8 pt-3 sm:pt-4">
            <div className="flex items-end gap-2 sm:gap-3">
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
                placeholder="Describe your legal situation or ask a question…"
                disabled={isLoading}
                className="input-field min-h-[46px] flex-1 resize-none py-3 text-sm sm:min-h-[52px] sm:py-3.5"
              />
              <button
                type="button"
                onClick={() => handleSend()}
                disabled={!input.trim() || isLoading}
                className="btn-primary h-[46px] shrink-0 justify-center px-4 disabled:cursor-not-allowed disabled:opacity-60 sm:h-[52px] sm:px-6"
              >
                Send →
              </button>
            </div>
            <p className="mt-1.5 text-center text-[9px] leading-4 text-slate-500 sm:mt-2 sm:text-[10px]">
              AI legal guidance based on Indian law — not a substitute for a licensed advocate. Outcomes depend on your facts, evidence and forum.
            </p>
          </div>
        </Card>
      </div>
    </div>
  )
}
