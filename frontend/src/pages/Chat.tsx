import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { addUserMessage, fetchChatHistory, sendChatMessage, setDocumentId } from '../store/chatSlice'
import { analyzeDocument } from '../store/analysisSlice'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { trackEvent } from '../utils/posthog'
import { Card } from '../components/Card'
import MarkdownMessage from '../components/MarkdownMessage'
import type { AnalysisResult } from '../types'

import { demoDocument } from '../utils/demoData'

// Shown only when no analysis is available for the current document.
const GENERIC_QUESTIONS = [
  'What is this document about?',
  'What are the main risks for me?',
  'What are my key obligations?',
  'Are there any important dates or deadlines?',
  'Which parts are in my favour?',
]

function truncate(text: string, max = 52): string {
  const t = text.trim()
  return t.length > max ? `${t.slice(0, max - 1).trimEnd()}…` : t
}

/**
 * Build suggested questions from the CURRENT document's analysis, so the chips are
 * specific to what the user actually uploaded (a rental clause, an FIR charge, a
 * cheque-bounce notice, etc.) rather than one static rental-only list.
 */
function buildSuggestedQuestions(analysis: AnalysisResult | null, docId?: string): string[] {
  if (!analysis || (docId && analysis.document_id !== docId)) return GENERIC_QUESTIONS

  const s = analysis.summary
  const docType = (s.document_type || 'document').trim()
  const out: string[] = []

  out.push(`What does this ${docType} mean for me?`)
  if ((s.high_risk_count ?? 0) > 0) out.push('What are the biggest risks I should worry about?')

  // Reference the actual highest-risk points from the document.
  const seen = new Set<string>()
  const ranked = [...(analysis.clauses || [])].sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0))
  for (const c of ranked) {
    if (out.length >= 4) break
    const label = (c.title || c.clause_type || '').trim()
    if (!label) continue
    const key = label.toLowerCase()
    if (seen.has(key)) continue
    seen.add(key)
    out.push(`Explain: "${truncate(label)}"`)
  }

  if (s.your_obligations && s.your_obligations.length) out.push('What do I need to do next?')
  if (s.other_party_rights && s.other_party_rights.length) out.push('What can the other party do?')
  if (s.beneficial_clauses && s.beneficial_clauses.length) out.push('Which points are in my favour?')

  // De-duplicate and cap.
  const unique = Array.from(new Set(out))
  return unique.slice(0, 5)
}

export default function Chat() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { messages, isLoading, error } = useAppSelector((s) => s.chat)
  const storeDoc = useAppSelector((s) => s.document.current)
  const currentDoc = storeDoc || demoDocument
  const analysis = useAppSelector((s) => s.analysis.result)
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  const suggestedQuestions = useMemo(
    () => buildSuggestedQuestions(analysis, currentDoc?.id),
    [analysis, currentDoc?.id]
  )
  const loadedAnalysisRef = useRef<string | null>(null)

  useEffect(() => {
    if (currentDoc && currentDoc.id !== 'demo') {
      dispatch(setDocumentId(currentDoc.id))
      dispatch(fetchChatHistory(currentDoc.id))
      // Load this document's SAVED analysis (cached — no re-analyze) so the
      // suggested questions reflect the actual uploaded document.
      if (analysis?.document_id !== currentDoc.id && loadedAnalysisRef.current !== currentDoc.id) {
        loadedAnalysisRef.current = currentDoc.id
        dispatch(analyzeDocument(currentDoc.id))
      }
    }
  }, [currentDoc, dispatch, analysis?.document_id])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = async (question?: string) => {
    const text = question || input.trim()
    if (!text || !currentDoc) return

    setInput('')
    dispatch(addUserMessage(text))
    trackEvent('chat_question_sent', {
      documentId: currentDoc.id,
      questionLength: text.length,
    })
    await dispatch(sendChatMessage({ document_id: currentDoc.id, question: text }))
  }

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="content-wrap min-h-screen px-3 py-3 sm:px-4 sm:py-4 lg:px-6 lg:py-5">
      <div className="mx-auto grid max-w-7xl gap-4 xl:grid-cols-[240px_minmax(0,1fr)]">
        {/* Sidebar */}
        <Card as="aside" variant="section" className="hidden h-fit rounded-[24px] p-4 xl:block">
          <p className="text-sm text-slate-500">SmartLegal AI</p>

          <h1 className="mt-2 text-2xl font-semibold text-white">
            Ask Anything About Your Document
          </h1>

          <p className="mt-3 text-sm leading-7 text-slate-400">
            The assistant answers using only your uploaded document context.
          </p>

          <div className="mt-6 space-y-3">
            <button
              type="button"
              onClick={() =>
                navigate(currentDoc ? `/analysis/${currentDoc.id}` : '/analysis')
              }
              className="btn-secondary w-full justify-center"
            >
              Back to Analysis
            </button>

            <button
              type="button"
              onClick={() => navigate('/upload')}
              className="btn-primary w-full justify-center"
            >
              Upload New File
            </button>
          </div>

          <Card variant="outline" className="mt-8 min-w-0 rounded-[24px] p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-500">
              Document
            </p>

            <p className="mt-3 break-all text-sm text-white">
              {currentDoc?.filename || 'Uploaded document'}
            </p>

            <p className="mt-1 text-sm text-slate-400">
              {analysis?.summary.document_type || 'Legal document'}
            </p>
          </Card>
        </Card>

        {/* Chat Section */}
        <Card as="section" variant="section" className="flex min-h-[calc(100vh-24px)] min-w-0 flex-col overflow-hidden rounded-[24px] p-3 sm:min-h-[calc(100vh-32px)] sm:rounded-[30px] sm:p-4 md:p-5 lg:min-h-[calc(100vh-40px)] lg:p-6">
        {/* Chat Header */}
        <div className="shrink-0 border-b border-white/8 pb-3 sm:pb-4">
          <p className="text-xs text-slate-500 sm:text-sm">
            AI Chat Workspace
          </p>

          <div className="mt-1 flex items-center justify-between gap-3">
            <h2 className="text-xl font-semibold text-white sm:text-2xl lg:text-3xl">
              Ask Anything About Your Document
            </h2>

            <span className="hidden shrink-0 rounded-full border border-[#8a5cff]/20 bg-[#8a5cff]/10 px-3 py-1 text-xs text-[#c5b4ff] sm:block">
              Document AI
            </span>
          </div>

          <p className="mt-1 max-w-3xl text-xs leading-5 text-slate-400 sm:mt-2 sm:text-sm sm:leading-6">
            Ask about rights, notice periods, penalties, or any unclear clause
            and get a document-grounded answer.
          </p>
        </div>

        {/* Chat Content */}
        <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col justify-center py-4 sm:py-5">
          {/* Empty State */}
          {messages.length === 0 && (
            <div className="space-y-4 text-center sm:space-y-5">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-[18px] border border-[#8a5cff]/25 bg-[#8a5cff]/10 text-2xl text-[#c5b4ff] sm:h-16 sm:w-16 sm:text-3xl">
                ⚖
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white sm:text-xl">
                  What would you like to know?
                </h3>

                <p className="mx-auto mt-1 max-w-xl text-xs leading-5 text-slate-400 sm:text-sm">
                  Ask anything about your uploaded legal document.
                </p>
              </div>

              <div className="flex flex-wrap justify-center gap-2">
                {suggestedQuestions.map((question) => (
                  <button
                    key={question}
                    type="button"
                    onClick={() => handleSend(question)}
                    className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-slate-300 transition hover:border-[#8a5cff]/30 hover:text-white sm:px-4 sm:py-2 sm:text-sm"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          {messages.length > 0 && (
            <div className="space-y-3 sm:space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`max-w-[92%] rounded-[18px] px-3 py-2.5 text-xs leading-5 sm:max-w-[80%] sm:rounded-[22px] sm:px-4 sm:py-3 sm:text-sm sm:leading-6 ${
                      msg.role === 'user'
                        ? 'bg-[linear-gradient(180deg,#f5c26b,#cf9b42)] text-slate-950 shadow-[0_12px_25px_rgba(245,194,107,0.18)]'
                        : 'border border-white/10 bg-white/[0.03] text-slate-200'
                    }`}
                  >
                    {msg.role === 'assistant' && (
                      <p className="mb-1 text-[9px] uppercase tracking-[0.2em] text-slate-500 sm:text-[10px]">
                        SmartLegal AI
                      </p>
                    )}

                    {msg.role === 'assistant' ? (
                      <MarkdownMessage content={msg.content} />
                    ) : (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    )}

                    <p
                      className={`mt-1 text-[9px] ${
                        msg.role === 'user'
                          ? 'text-slate-800/60'
                          : 'text-slate-500'
                      }`}
                    >
                      {new Date(msg.timestamp).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                </div>
              ))}

              {/* Thinking */}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="rounded-[18px] border border-white/10 bg-white/[0.03] px-3 py-2.5">
                    <div className="flex items-center gap-2">
                      <span className="text-[9px] uppercase tracking-[0.2em] text-slate-500">
                        Thinking
                      </span>

                      {[0, 1, 2].map((dot) => (
                        <span
                          key={dot}
                          className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#8a5cff]"
                          style={{
                            animationDelay: `${dot * 0.15}s`,
                          }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Error */}
              {error && (
                <div className="rounded-[18px] border border-[#fb7185]/25 bg-[#2a1320]/65 px-3 py-2.5 text-xs text-[#fecdd3] sm:text-sm">
                  {error}
                </div>
              )}

              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* Chat Input */}
        <div className="mx-auto w-full max-w-4xl shrink-0 border-t border-white/8 pt-3 sm:pt-4">
          <div className="flex items-end gap-2 sm:gap-3">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              placeholder="Ask a question about your document..."
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

          <p className="mt-1.5 text-center text-[9px] text-slate-500 sm:mt-2 sm:text-[10px]">
            Answers are based on your uploaded document and are not legal advice.
          </p>
        </div>
      </Card>
    </div>
  </div>
)
}
