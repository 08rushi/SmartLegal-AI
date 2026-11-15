import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
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
  const { t } = useTranslation('escalation')
  const [submitted, setSubmitted] = useState(false)
  const [note, setNote] = useState('')
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => () => {
    if (timer.current) clearTimeout(timer.current)
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitted(true)
    timer.current = setTimeout(() => {
      setSubmitted(false)
      onClose()
    }, 2500)
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`⚖️ ${t('title')}`}>
      {!submitted ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <p className="text-sm text-slate-300">
            {t('intro', { name: documentName || t('fallbackName') })}
          </p>

          <div className="space-y-2">
            <label htmlFor="escalation-note" className="block text-xs font-bold text-amber-300 uppercase">
              {t('concerns')}
            </label>
            <textarea
              id="escalation-note"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
              placeholder={t('placeholder')}
              aria-describedby="escalation-privacy"
              className="w-full bg-[#1e293b] border border-slate-700 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-amber-400"
            />
          </div>

          <div id="escalation-privacy" className="bg-amber-400/10 border border-amber-400/20 p-3 rounded-xl text-xs text-amber-200">
            🔒 {t('privacy')}
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-300 rounded-xl"
            >
              {t('cancel')}
            </button>
            <button
              type="submit"
              className="px-6 py-2.5 bg-amber-400 hover:bg-amber-500 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-amber-400/20"
            >
              {t('submit')}
            </button>
          </div>
        </form>
      ) : (
        <div className="text-center py-6 space-y-3" role="status">
          <div className="text-4xl" aria-hidden="true">✅</div>
          <h4 className="text-lg font-bold text-white">{t('successTitle')}</h4>
          <p className="text-xs text-slate-400">{t('successBody')}</p>
        </div>
      )}
    </Modal>
  )
}
