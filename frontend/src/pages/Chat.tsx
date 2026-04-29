import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { addUserMessage, sendChatMessage, setDocumentId } from '../store/chatSlice'
import { useAppDispatch, useAppSelector } from '../hooks/redux'

const suggestedQuestions = [
  'Can my landlord increase rent mid-year?',
  'What happens if I break the contract early?',
  'How much notice do I need to give?',
  'Is there any penalty clause I should watch for?',
  'What are my rights if the other party wants to terminate?',
]

export default function Chat() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { messages, isLoading, error } = useAppSelector((s) => s.chat)
  const currentDoc = useAppSelector((s) => s.document.current)
  const analysis = useAppSelector((s) => s.analysis.result)
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!currentDoc) {
      navigate('/upload')
      return
    }
    dispatch(setDocumentId(currentDoc.id))
  }, [currentDoc, dispatch, navigate])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = async (question?: string) => {
    const text = question || input.trim()
    if (!text || !currentDoc) return

    setInput('')
    dispatch(addUserMessage(text))
    await dispatch(sendChatMessage({ document_id: currentDoc.id, question: text }))
  }

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="content-wrap py-8 sm:py-10">
      <div className="mx-auto grid max-w-7xl gap-6 xl:grid-cols-[260px_minmax(0,1fr)]">
        <aside className="section-card h-fit rounded-[30px] p-5">
          <p className="text-sm text-slate-500">SmartLegal AI</p>
          <h1 className="mt-2 text-2xl font-semibold text-white">Ask Anything About Your Document</h1>
          <p className="mt-3 text-sm leading-7 text-slate-400">
            The assistant answers using only your uploaded document context.
          </p>

          <div className="mt-6 space-y-3">
            <button type="button" onClick={() => navigate('/analysis')} className="btn-secondary w-full justify-center">
              Back to Analysis
            </button>
            <button type="button" onClick={() => navigate('/upload')} className="btn-primary w-full justify-center">
              Upload New File
            </button>
          </div>

          <div className="mt-8 rounded-[24px] border border-white/10 bg-white/[0.03] p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Document</p>
            <p className="mt-3 text-sm text-white">{currentDoc?.filename || 'Uploaded document'}</p>
            <p className="mt-1 text-sm text-slate-400">{analysis?.summary.document_type || 'Legal document'}</p>
          </div>
        </aside>

        <section className="section-card flex min-h-[72vh] flex-col rounded-[30px] p-4 sm:p-6">
          <div className="border-b border-white/8 pb-5">
            <p className="text-sm text-slate-500">AI Chat Workspace</p>
            <h2 className="mt-2 text-3xl font-semibold text-white">Ask Anything About Your Document</h2>
            <p className="mt-2 text-sm leading-7 text-slate-400">
              Ask about rights, notice periods, penalties, or any unclear clause and get a document-grounded answer.
            </p>
          </div>

          <div className="flex-1 overflow-y-auto py-6">
            {messages.length === 0 && (
              <div className="mx-auto max-w-3xl space-y-8 text-center">
                <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-[30px] border border-[#8a5cff]/25 bg-[#8a5cff]/10 text-4xl text-[#c5b4ff]">
                  ⚖
                </div>
                <div>
                  <h3 className="text-2xl font-semibold text-white">Start with a suggested question</h3>
                  <p className="mt-3 text-sm leading-7 text-slate-400">
                    This layout mirrors your reference board’s AI panel while keeping the real conversation flow responsive.
                  </p>
                </div>
                <div className="flex flex-wrap justify-center gap-3">
                  {suggestedQuestions.map((question) => (
                    <button
                      key={question}
                      type="button"
                      onClick={() => handleSend(question)}
                      className="rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-slate-300 transition hover:border-[#8a5cff]/30 hover:text-white"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="mx-auto mt-2 max-w-3xl space-y-4">
              {messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-[88%] rounded-[24px] px-4 py-4 text-sm leading-7 sm:max-w-[80%] ${
                      msg.role === 'user'
                        ? 'bg-[linear-gradient(180deg,#f5c26b,#cf9b42)] text-slate-950 shadow-[0_20px_40px_rgba(245,194,107,0.24)]'
                        : 'border border-white/10 bg-white/[0.03] text-slate-200'
                    }`}
                  >
                    {msg.role === 'assistant' && (
                      <p className="mb-2 text-xs uppercase tracking-[0.2em] text-slate-500">SmartLegal AI</p>
                    )}
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    <p className={`mt-2 text-xs ${msg.role === 'user' ? 'text-slate-800/70' : 'text-slate-500'}`}>
                      {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="rounded-[24px] border border-white/10 bg-white/[0.03] px-4 py-4">
                    <div className="flex items-center gap-2">
                      <span className="text-xs uppercase tracking-[0.2em] text-slate-500">Thinking</span>
                      {[0, 1, 2].map((dot) => (
                        <span
                          key={dot}
                          className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#8a5cff]"
                          style={{ animationDelay: `${dot * 0.15}s` }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {error && (
                <div className="rounded-[22px] border border-[#fb7185]/25 bg-[#2a1320]/65 px-4 py-3 text-sm text-[#fecdd3]">
                  {error}
                </div>
              )}

              <div ref={bottomRef} />
            </div>
          </div>

          <div className="border-t border-white/8 pt-5">
            <div className="mx-auto flex max-w-3xl flex-col gap-3 sm:flex-row">
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
                placeholder="Ask a question about your document..."
                disabled={isLoading}
                className="input-field min-h-[54px] flex-1 resize-none py-4"
              />
              <button
                type="button"
                onClick={() => handleSend()}
                disabled={!input.trim() || isLoading}
                className="btn-primary min-h-[54px] justify-center px-6 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Send →
              </button>
            </div>
            <p className="mt-3 text-center text-xs text-slate-500">
              Answers are based on your uploaded document and are not legal advice.
            </p>
          </div>
        </section>
      </div>
    </div>
  )
}
