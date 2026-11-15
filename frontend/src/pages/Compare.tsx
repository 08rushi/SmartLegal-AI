import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAppSelector } from '../hooks/redux'
import type { UploadedDocument } from '../types'
import { enumLabel, formatBytes, formatDateTime } from '../utils/i18nHelpers'

// The original page showed sample comparison results. Real document comparison does not exist yet, so the
// layout is kept but no result is ever produced: the compare button stays disabled and a notice says so.
export default function Compare() {
  const { t, i18n } = useTranslation('compare')
  const documents = useAppSelector((s) => s.document.history)
  const [docAId, setDocAId] = useState<string>('')
  const [docBId, setDocBId] = useState<string>('')

  const docA = documents.find((d: UploadedDocument) => d.id === docAId)
  const docB = documents.find((d: UploadedDocument) => d.id === docBId)
  const typeLabel = (d: UploadedDocument) =>
    d.document_type ? enumLabel(t, 'clauses:docTypes', d.document_type) : t('unclassified')
  const meta = (d: UploadedDocument) =>
    t('uploadedMeta', { date: formatDateTime(d.uploaded_at, i18n.language, false), size: formatBytes(d.file_size, t, i18n.language) })

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-10">
        {/* Header */}
        <div className="text-center space-y-4">
          <span className="px-4 py-1.5 bg-amber-400/10 text-amber-300 rounded-full text-xs font-semibold uppercase tracking-wider border border-amber-400/20">
            {t('eyebrow')}
          </span>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight">
            {t('title')}
          </h1>
          <p className="text-slate-400 max-w-2xl mx-auto text-base sm:text-lg">
            {t('subtitle')}
          </p>
        </div>

        <div
          role="note"
          className="mx-auto max-w-3xl rounded-2xl border border-amber-400/30 bg-amber-400/10 px-4 py-3 text-center text-sm text-amber-200"
        >
          {t('description')}
        </div>

        {/* Selection Area */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-[#121a2d]/80 border border-slate-800 p-6 sm:p-8 rounded-3xl backdrop-blur-xl">
          {/* Document A Selector */}
          <div className="space-y-3">
            <label htmlFor="compare-doc-a" className="block text-sm font-semibold text-amber-300 uppercase tracking-wider">
              {t('selectA')}
            </label>
            <select
              id="compare-doc-a"
              value={docAId}
              onChange={(e) => setDocAId(e.target.value)}
              className="w-full bg-[#1e293b] border border-slate-700 rounded-xl p-3.5 text-white focus:outline-none focus:border-amber-400"
            >
              <option value="">{t('chooseFirst')}</option>
              {documents.map((d: UploadedDocument) => (
                <option key={d.id} value={d.id}>
                  📄 {d.filename} ({typeLabel(d)})
                </option>
              ))}
            </select>
            {docA && <p className="text-xs text-slate-400">{meta(docA)}</p>}
          </div>

          {/* Document B Selector */}
          <div className="space-y-3">
            <label htmlFor="compare-doc-b" className="block text-sm font-semibold text-amber-300 uppercase tracking-wider">
              {t('selectB')}
            </label>
            <select
              id="compare-doc-b"
              value={docBId}
              onChange={(e) => setDocBId(e.target.value)}
              className="w-full bg-[#1e293b] border border-slate-700 rounded-xl p-3.5 text-white focus:outline-none focus:border-amber-400"
            >
              <option value="">{t('chooseSecond')}</option>
              {documents.map((d: UploadedDocument) => (
                <option key={d.id} value={d.id} disabled={d.id === docAId}>
                  📄 {d.filename} ({typeLabel(d)})
                </option>
              ))}
            </select>

            {docB && <p className="text-xs text-slate-400">{meta(docB)}</p>}
          </div>

          <div className="md:col-span-2 text-center pt-4 space-y-3">
            <button
              type="button"
              disabled
              aria-disabled="true"
              className="px-8 py-4 bg-gradient-to-r from-amber-400 to-amber-500 text-slate-950 font-bold text-base rounded-2xl shadow-xl shadow-amber-400/20 opacity-50 cursor-not-allowed transition-all"
            >
              {t('compareButton')}
            </button>
            <p className="text-xs font-semibold uppercase tracking-wider text-amber-300">{t('comingSoon')}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
