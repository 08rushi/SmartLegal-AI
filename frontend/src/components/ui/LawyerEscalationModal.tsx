import { useState } from 'react'
import { Modal } from './Modal'

interface LawyerEscalationModalProps {
  isOpen: boolean
  onClose: () => void
  documentName: string
}

export function LawyerEscalationModal({
  isOpen,
  onClose,
  documentName,
}: LawyerEscalationModalProps) {
  const [submitted, setSubmitted] = useState(false)
  const [note, setNote] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitted(true)
    setTimeout(() => {
      setSubmitted(false)
      onClose()
    }, 2500)
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="⚖️ Connect with a Verified Advocate">
      {!submitted ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <p className="text-sm text-slate-300">
            Request formal human legal review for <strong>{documentName}</strong>. A verified advocate registered with the Bar Council of India will review your document.
          </p>

          <div className="space-y-2">
            <label className="block text-xs font-bold text-amber-300 uppercase">
              Specific Concerns or Questions (Optional)
            </label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
              placeholder="e.g. Please check if the 90-day notice period is legally enforceable under Delhi Rent Control Act..."
              className="w-full bg-[#1e293b] border border-slate-700 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-amber-400"
            />
          </div>

          <div className="bg-amber-400/10 border border-amber-400/20 p-3 rounded-xl text-xs text-amber-200">
            🔒 Your private document will be encrypted and shared strictly with the assigned advocate upon your explicit consent.
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-300 rounded-xl"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-6 py-2.5 bg-amber-400 hover:bg-amber-500 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-amber-400/20"
            >
              Request Advocate Review
            </button>
          </div>
        </form>
      ) : (
        <div className="text-center py-6 space-y-3">
          <div className="text-4xl">✅</div>
          <h4 className="text-lg font-bold text-white">Review Request Submitted!</h4>
          <p className="text-xs text-slate-400">
            An advocate from our partner panel will contact you within 24 business hours.
          </p>
        </div>
      )}
    </Modal>
  )
}
