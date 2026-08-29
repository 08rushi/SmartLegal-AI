import { useState } from 'react'

interface VoiceInputButtonProps {
  onSpeechResult: (text: string) => void
}

export function VoiceInputButton({ onSpeechResult }: VoiceInputButtonProps) {
  const [listening, setListening] = useState(false)

  const toggleListening = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition

    if (!SpeechRecognition) {
      alert('Voice recognition is not supported in your browser. Please type your query.')
      return
    }

    if (listening) {
      setListening(false)
      return
    }

    try {
      const recognition = new SpeechRecognition()
      recognition.continuous = false
      recognition.interimResults = false
      recognition.lang = 'en-IN'

      recognition.onstart = () => setListening(true)
      recognition.onend = () => setListening(false)
      recognition.onerror = () => setListening(false)

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript
        if (transcript) {
          onSpeechResult(transcript)
        }
      }

      recognition.start()
    } catch {
      setListening(false)
    }
  }

  return (
    <button
      type="button"
      onClick={toggleListening}
      className={`p-2.5 rounded-xl border transition-all ${
        listening
          ? 'bg-rose-500/20 border-rose-500 text-rose-400 animate-pulse shadow-lg shadow-rose-500/20'
          : 'bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-300'
      }`}
      title={listening ? 'Listening... Speak now' : 'Voice Search (Hindi / English)'}
    >
      <span className="text-sm">{listening ? '🎙️ Listening...' : '🎤'}</span>
    </button>
  )
}
