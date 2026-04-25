import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { sendChatMessage, addUserMessage, setDocumentId } from '../store/chatSlice'

const SUGGESTED_QUESTIONS = [
  'Can my landlord increase rent mid-year?',
  'What happens if I break the contract early?',
  'How much notice do I need to give before leaving?',
  'What are my rights if the landlord wants to evict me?',
  'Is there a penalty clause? What does it say?',
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
  }, [messages])

  const handleSend = async (question?: string) => {
    const text = question || input.trim()
    if (!text || !currentDoc) return

    setInput('')
    dispatch(addUserMessage(text))
    await dispatch(sendChatMessage({ document_id: currentDoc.id, question: text }))
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="font-bold text-gray-900">Ask about your document</h1>
            <p className="text-sm text-gray-400">
              📄 {currentDoc?.filename || 'Document'} •{' '}
              {analysis?.summary.document_type || 'Legal document'}
            </p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => navigate('/analysis')} className="btn-secondary text-sm py-2">
              ← Back to analysis
            </button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-6 px-4">
        <div className="max-w-3xl mx-auto space-y-4">
          {/* Welcome message */}
          {messages.length === 0 && (
            <div className="text-center py-8">
              <div className="text-5xl mb-4">💬</div>
              <h2 className="text-xl font-semibold text-gray-800 mb-2">
                Ask anything about your document
              </h2>
              <p className="text-gray-400 text-sm mb-8">
                I'll answer using only the content of your uploaded document.
              </p>

              {/* Suggested questions */}
              <div className="flex flex-wrap justify-center gap-2">
                {SUGGESTED_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    className="text-sm bg-white border border-gray-200 hover:border-brand-300 hover:bg-brand-50 text-gray-600 hover:text-brand-700 px-4 py-2 rounded-full transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Chat messages */}
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-brand-500 text-white rounded-br-sm'
                    : 'bg-white border border-gray-200 text-gray-700 rounded-bl-sm shadow-sm'
                }`}
              >
                {msg.role === 'assistant' && (
                  <p className="text-xs text-gray-400 mb-1 font-medium">⚖️ SmartLegal AI</p>
                )}
                <p className="whitespace-pre-wrap">{msg.content}</p>
                <p className={`text-xs mt-1 ${msg.role === 'user' ? 'text-brand-200' : 'text-gray-400'}`}>
                  {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))}

          {/* Loading bubble */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
                <div className="flex gap-1 items-center">
                  <span className="text-xs text-gray-400 mr-2">⚖️ Thinking</span>
                  {[0, 1, 2].map((i) => (
                    <span
                      key={i}
                      className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="text-center text-sm text-red-500 bg-red-50 border border-red-200 rounded-xl p-3">
              ⚠️ {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input bar */}
      <div className="bg-white border-t border-gray-200 px-4 py-4">
        <div className="max-w-3xl mx-auto flex gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your document... (Enter to send)"
            rows={1}
            disabled={isLoading}
            className="flex-1 input-field resize-none py-3 min-h-[48px] max-h-32"
            style={{ height: 'auto' }}
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className="btn-primary px-5 self-end"
          >
            Send →
          </button>
        </div>
        <p className="text-xs text-gray-400 text-center mt-2">
          Answers are based only on your uploaded document. Not legal advice.
        </p>
      </div>
    </div>
  )
}
