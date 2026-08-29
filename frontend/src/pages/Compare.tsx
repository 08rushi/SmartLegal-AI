import { useState } from 'react'
import { useAppSelector } from '../hooks/redux'
import type { UploadedDocument } from '../types'


export default function Compare() {
  const documents = useAppSelector((s) => s.document.history)
  const [docAId, setDocAId] = useState<string>('')
  const [docBId, setDocBId] = useState<string>('')
  const [comparing, setComparing] = useState(false)
  const [compareResult, setCompareResult] = useState<any | null>(null)

  const docA = documents.find((d: UploadedDocument) => d.id === docAId)
  const docB = documents.find((d: UploadedDocument) => d.id === docBId)

  const handleRunComparison = () => {
    if (!docAId || !docBId || docAId === docBId) return
    setComparing(true)

    // Simulate AI dual-document diffing computation
    setTimeout(() => {
      setCompareResult({
        summary: `Comparative Analysis between '${docA?.filename}' and '${docB?.filename}'. Document B contains significantly stricter penalty terms and a longer lock-in period compared to Document A.`,
        docA: {
          name: docA?.filename || 'Document A',
          riskScore: 'Medium Risk (4/10)',
          noticePeriod: '30 Days',
          depositCap: '2 Months Rent',
          lockIn: '6 Months',
          highRiskClauses: ['Automatic 10% annual escalation'],
        },
        docB: {
          name: docB?.filename || 'Document B',
          riskScore: 'High Risk (8/10)',
          noticePeriod: '90 Days',
          depositCap: '4 Months Rent',
          lockIn: '12 Months',
          highRiskClauses: ['Forfeiture of full deposit on early exit', 'Unilateral maintenance charges'],
        },
        diffs: [
          {
            topic: 'Security Deposit',
            docATerm: '2 Months Rent (refundable within 30 days)',
            docBTerm: '4 Months Rent (refundable within 90 days)',
            winner: 'Document A is more favorable for tenant',
          },
          {
            topic: 'Notice Period',
            docATerm: '30 days written notice after lock-in',
            docBTerm: '90 days written notice required',
            winner: 'Document A provides higher flexibility',
          },
          {
            topic: 'Lock-in Duration',
            docATerm: '6 Months',
            docBTerm: '12 Months with 100% penalty on early exit',
            winner: 'Document A is far safer',
          },
        ],
      })
      setComparing(false)
    }, 1200)
  }

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-10">
        {/* Header */}
        <div className="text-center space-y-4">
          <span className="px-4 py-1.5 bg-amber-400/10 text-amber-300 rounded-full text-xs font-semibold uppercase tracking-wider border border-amber-400/20">
            AI Side-by-Side Comparison
          </span>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight">
            Compare Two Legal Documents
          </h1>
          <p className="text-slate-400 max-w-2xl mx-auto text-base sm:text-lg">
            Select two agreements or contracts to identify clause discrepancies, risk variance, and one-sided terms.
          </p>
        </div>

        {/* Selection Area */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-[#121a2d]/80 border border-slate-800 p-6 sm:p-8 rounded-3xl backdrop-blur-xl">
          {/* Document A Selector */}
          <div className="space-y-3">
            <label className="block text-sm font-semibold text-amber-300 uppercase tracking-wider">
              Select Document A (Base)
            </label>
            <select
              value={docAId}
              onChange={(e) => setDocAId(e.target.value)}
              className="w-full bg-[#1e293b] border border-slate-700 rounded-xl p-3.5 text-white focus:outline-none focus:border-amber-400"
            >
              <option value="">-- Choose first document --</option>
              {documents.map((d: UploadedDocument) => (
                <option key={d.id} value={d.id}>
                  📄 {d.filename} ({d.document_type || 'Unclassified'})
                </option>
              ))}
            </select>
            {docA && (
              <p className="text-xs text-slate-400">
                Uploaded: {new Date(docA.uploaded_at).toLocaleDateString()} • Size: {(docA.file_size / 1024).toFixed(1)} KB
              </p>
            )}
          </div>

          {/* Document B Selector */}
          <div className="space-y-3">
            <label className="block text-sm font-semibold text-amber-300 uppercase tracking-wider">
              Select Document B (Comparison)
            </label>
            <select
              value={docBId}
              onChange={(e) => setDocBId(e.target.value)}
              className="w-full bg-[#1e293b] border border-slate-700 rounded-xl p-3.5 text-white focus:outline-none focus:border-amber-400"
            >
              <option value="">-- Choose second document --</option>
              {documents.map((d: UploadedDocument) => (
                <option key={d.id} value={d.id} disabled={d.id === docAId}>
                  📄 {d.filename} ({d.document_type || 'Unclassified'})
                </option>
              ))}
            </select>

            {docB && (
              <p className="text-xs text-slate-400">
                Uploaded: {new Date(docB.uploaded_at).toLocaleDateString()} • Size: {(docB.file_size / 1024).toFixed(1)} KB
              </p>
            )}
          </div>

          <div className="md:col-span-2 text-center pt-4">
            <button
              onClick={handleRunComparison}
              disabled={!docAId || !docBId || docAId === docBId || comparing}
              className="px-8 py-4 bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-500 hover:to-amber-600 text-slate-950 font-bold text-base rounded-2xl shadow-xl shadow-amber-400/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {comparing ? '⚡ Computing Clause Differences...' : '⚡ Compare Documents Side-by-Side'}
            </button>
          </div>
        </div>

        {/* Results View */}
        {compareResult && (
          <div className="space-y-8 animate-fadeIn">
            {/* AI Executive Comparison Summary */}
            <div className="bg-gradient-to-br from-slate-900 to-[#162035] border border-amber-400/30 p-6 sm:p-8 rounded-3xl shadow-2xl space-y-4">
              <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">AI Executive Verdict</span>
              <p className="text-lg text-slate-200 leading-relaxed font-medium">
                {compareResult.summary}
              </p>
            </div>

            {/* Score Comparison Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-[#121a2d] border border-emerald-500/30 p-6 rounded-2xl space-y-3">
                <h3 className="text-xl font-bold text-emerald-400">{compareResult.docA.name}</h3>
                <div className="text-sm space-y-1 text-slate-300">
                  <p><strong>Overall Risk:</strong> <span className="text-emerald-300">{compareResult.docA.riskScore}</span></p>
                  <p><strong>Notice Period:</strong> {compareResult.docA.noticePeriod}</p>
                  <p><strong>Deposit Cap:</strong> {compareResult.docA.depositCap}</p>
                  <p><strong>Lock-in:</strong> {compareResult.docA.lockIn}</p>
                </div>
              </div>

              <div className="bg-[#121a2d] border border-rose-500/30 p-6 rounded-2xl space-y-3">
                <h3 className="text-xl font-bold text-rose-400">{compareResult.docB.name}</h3>
                <div className="text-sm space-y-1 text-slate-300">
                  <p><strong>Overall Risk:</strong> <span className="text-rose-300">{compareResult.docB.riskScore}</span></p>
                  <p><strong>Notice Period:</strong> {compareResult.docB.noticePeriod}</p>
                  <p><strong>Deposit Cap:</strong> {compareResult.docB.depositCap}</p>
                  <p><strong>Lock-in:</strong> {compareResult.docB.lockIn}</p>
                </div>
              </div>
            </div>

            {/* Side-by-Side Clause Diffing Table */}
            <div className="bg-[#121a2d] border border-slate-800 rounded-3xl p-6 overflow-x-auto">
              <h3 className="text-xl font-bold text-white mb-6">Detailed Clause Discrepancy Matrix</h3>
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 text-xs uppercase">
                    <th className="py-3 px-4">Clause Category</th>
                    <th className="py-3 px-4 text-emerald-400">{docA?.filename}</th>
                    <th className="py-3 px-4 text-rose-400">{docB?.filename}</th>
                    <th className="py-3 px-4 text-amber-300">AI Advantage Verdict</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-sm">
                  {compareResult.diffs.map((diff: any, idx: number) => (
                    <tr key={idx} className="hover:bg-slate-800/40">
                      <td className="py-4 px-4 font-semibold text-white">{diff.topic}</td>
                      <td className="py-4 px-4 text-slate-300">{diff.docATerm}</td>
                      <td className="py-4 px-4 text-slate-300">{diff.docBTerm}</td>
                      <td className="py-4 px-4 font-medium text-amber-400">{diff.winner}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
