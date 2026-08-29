import React, { useState } from 'react'
import { Link } from 'react-router-dom'

export interface ChecklistItem {
  id: string
  item_text: string
  is_done: number | boolean
  updated_at: string
}

interface ServiceDetailProps {
  id: string
  title: string
  domainLabel: string
  typeLabel: string
  status: string
  created_at: string
  updated_at: string
  notes?: string
  checklist: ChecklistItem[]
  requiredDocs?: string[]
  officialPortalUrl?: string
  onToggleChecklist: (itemId: string, currentDone: boolean) => void
  onUpdateStatus?: (newStatus: string) => void
  onSaveNotes?: (notes: string) => void
  backPath?: string
}


export const ServiceDetail: React.FC<ServiceDetailProps> = ({
  id,
  title,
  domainLabel,
  typeLabel,
  status,
  created_at,
  updated_at,
  notes = '',
  checklist,
  requiredDocs = [],
  officialPortalUrl,
  onToggleChecklist,
  onUpdateStatus,
  onSaveNotes,
  backPath = '/service-tracker',
}) => {
  const [editingNotes, setEditingNotes] = useState(notes)
  const [isSaved, setIsSaved] = useState(false)

  const completedCount = checklist.filter((item) => item.is_done).length
  const progressPercent = checklist.length > 0 ? Math.round((completedCount / checklist.length) * 100) : 0

  const handleSaveNotes = () => {
    if (onSaveNotes) {
      onSaveNotes(editingNotes)
      setIsSaved(true)
      setTimeout(() => setIsSaved(false), 2000)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Breadcrumb Navigation */}
        <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400">
          <Link to={backPath} className="hover:underline">← Back to Tracker</Link>
          <span>/</span>
          <span className="text-slate-400">{domainLabel}</span>
          <span>/</span>
          <span className="text-slate-500 truncate max-w-[200px]">{title}</span>
        </div>

        {/* Application Header Card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6 shadow-2xl">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 text-xs font-bold uppercase rounded-lg">
                {typeLabel}
              </span>
              <span className="px-3 py-1 bg-slate-950 text-slate-400 border border-slate-800 text-xs font-medium rounded-lg">
                ID: {id}
              </span>
            </div>

            {/* Status Switcher Badge */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-400">Status:</span>
              <select
                value={status}
                onChange={(e) => onUpdateStatus && onUpdateStatus(e.target.value)}
                className="bg-slate-950 border border-slate-700 text-xs font-bold text-emerald-400 rounded-xl px-3 py-1.5 focus:outline-none focus:border-indigo-500"
              >
                <option value="in_progress">In Progress ⏳</option>
                <option value="submitted">Submitted 📩</option>
                <option value="under_review">Under Review 🔍</option>
                <option value="completed">Completed ✅</option>
              </select>
            </div>
          </div>

          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white leading-tight">
              {title}
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Application Created: {new Date(created_at).toLocaleDateString()} • Last Updated: {new Date(updated_at).toLocaleDateString()}
            </p>
          </div>

          {/* Progress Bar */}
          <div className="space-y-2 pt-2 border-t border-slate-800/80">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-300">Checklist Progress</span>
              <span className="font-extrabold text-indigo-400">{completedCount} of {checklist.length} Completed ({progressPercent}%)</span>
            </div>
            <div className="w-full bg-slate-950 rounded-full h-3 p-0.5 border border-slate-800">
              <div
                className="bg-gradient-to-r from-indigo-500 to-emerald-400 h-full rounded-full transition-all duration-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {/* Official Portal CTA */}
          {officialPortalUrl && (
            <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
              <span className="text-xs text-slate-400">Official Government Website:</span>
              <a
                href={officialPortalUrl}
                target="_blank"
                rel="noreferrer"
                className="px-4 py-2 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 text-xs font-bold rounded-xl transition-all flex items-center gap-1.5"
              >
                <span>Visit Portal (.gov.in)</span>
                <span>🔗</span>
              </a>
            </div>
          )}
        </div>

        {/* Interactive Checklist & Notes Layout */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Checklist Card (Spans 2 cols) */}
          <div className="md:col-span-2 bg-slate-900/60 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-xl">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <span>☑️</span> Application Step Checklist
            </h3>

            <div className="space-y-2">
              {checklist.map((item) => (
                <div
                  key={item.id}
                  onClick={() => onToggleChecklist(item.id, Boolean(item.is_done))}
                  className={`p-4 rounded-2xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                    item.is_done
                      ? 'bg-emerald-950/20 border-emerald-800/40 text-emerald-200'
                      : 'bg-slate-950/80 border-slate-800 text-slate-200 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={Boolean(item.is_done)}
                      onChange={() => {}}
                      className="w-4 h-4 rounded text-emerald-500 focus:ring-emerald-500 bg-slate-900 border-slate-700"
                    />
                    <span className={`text-xs font-semibold ${item.is_done ? 'line-through opacity-70' : ''}`}>
                      {item.item_text}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500">{new Date(item.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Required Documents & Application Notes Sidebar */}
          <div className="space-y-6">
            
            {/* Required Documents */}
            {requiredDocs.length > 0 && (
              <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 space-y-3 shadow-xl">
                <h4 className="text-xs font-bold uppercase text-indigo-400 tracking-wider">
                  Required Documents
                </h4>
                <ul className="text-xs text-slate-300 space-y-2">
                  {requiredDocs.map((doc, idx) => (
                    <li key={idx} className="flex items-center gap-2 bg-slate-950/80 p-2.5 rounded-xl border border-slate-800">
                      <span className="text-indigo-400">📄</span>
                      <span>{doc}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* User Personal Notes */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 space-y-3 shadow-xl">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase text-indigo-400 tracking-wider">
                  Application Notes
                </h4>
                {isSaved && <span className="text-[10px] text-emerald-400 font-bold">Saved! ✓</span>}
              </div>

              <textarea
                rows={4}
                value={editingNotes}
                onChange={(e) => setEditingNotes(e.target.value)}
                placeholder="Add reference numbers, appointment dates, or custom reminders..."
                className="w-full bg-slate-950 border border-slate-800 text-xs text-slate-200 p-3 rounded-xl focus:outline-none focus:border-indigo-500 leading-relaxed"
              />

              <button
                onClick={handleSaveNotes}
                className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-xl transition-all shadow-md"
              >
                Save Notes
              </button>
            </div>

          </div>

        </div>

      </div>
    </div>
  )
}

export default ServiceDetail
