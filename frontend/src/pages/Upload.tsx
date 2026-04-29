import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { analyzeDocument } from '../store/analysisSlice'
import { uploadDocument } from '../store/documentSlice'

const documentTypes = [
  'Rental Agreement',
  'Employment Contract',
  'Loan Agreement',
  'Service Contract',
]

const steps = ['Upload', 'Analyze', 'Review', 'Results']

export default function Upload() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { status, uploadProgress, error } = useAppSelector((s) => s.document)
  const analysisLoading = useAppSelector((s) => s.analysis.isLoading)
  const [fileName, setFileName] = useState('')

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0]
      if (!file) return

      setFileName(file.name)
      const uploadResult = await dispatch(uploadDocument(file))
      if (uploadDocument.rejected.match(uploadResult)) return

      const doc = uploadResult.payload as { id: string }
      const analyzeResult = await dispatch(analyzeDocument(doc.id))
      if (analyzeDocument.fulfilled.match(analyzeResult)) {
        navigate('/analysis')
      }
    },
    [dispatch, navigate]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'image/*': ['.jpg', '.jpeg', '.png'] },
    maxFiles: 1,
    disabled: status === 'uploading' || analysisLoading,
  })

  const isLoading = status === 'uploading' || analysisLoading
  const loadingLabel =
    status === 'uploading'
      ? `Uploading... ${uploadProgress}%`
      : analysisLoading
        ? 'AI is reading your document...'
        : ''

  return (
    <div className="content-wrap py-8 sm:py-10">
      <div className="mx-auto grid max-w-7xl gap-6 xl:grid-cols-[0.86fr_1.14fr]">
        <div className="section-card rounded-[32px] p-6 sm:p-8">
          <span className="section-eyebrow">03 Upload Document</span>
          <h1 className="mt-4 text-3xl font-semibold text-white sm:text-4xl">Upload Your Document</h1>
          <p className="mt-3 text-sm leading-7 text-slate-400 sm:text-base">
            Supports rental agreements, employment contracts, loan papers, and any legal PDF. The flow is fully responsive for mobile, tablet, and desktop.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            {steps.map((step, index) => (
              <div key={step} className="flex items-center gap-3">
                <div className={`flex h-10 min-w-10 items-center justify-center rounded-full border px-3 text-xs font-semibold ${
                  index === 0 ? 'border-[#8a5cff]/40 bg-[#8a5cff]/15 text-[#c5b4ff]' : 'border-white/10 bg-white/[0.03] text-slate-500'
                }`}>
                  {step}
                </div>
                {index < steps.length - 1 && <div className="hidden h-px w-8 bg-white/10 sm:block" />}
              </div>
            ))}
          </div>

          <div className="mt-8 grid gap-4 sm:grid-cols-2">
            {documentTypes.map((type) => (
              <div key={type} className="info-card rounded-[24px] px-4 py-4 text-sm text-slate-300">
                {type}
              </div>
            ))}
          </div>
        </div>

        <div className="section-card rounded-[32px] p-5 sm:p-8">
          <div
            {...getRootProps()}
            className={`upload-dropzone relative overflow-hidden rounded-[30px] border border-dashed px-5 py-10 text-center transition-all duration-300 sm:px-8 sm:py-14 ${
              isDragActive
                ? 'border-[#f5c26b]/55 bg-[#15101d]/80 shadow-[0_0_40px_rgba(245,194,107,0.16)]'
                : 'border-white/12 bg-[#0b1120]/72 hover:border-[#8a5cff]/35 hover:bg-[#10172a]/80'
            } ${isLoading ? 'pointer-events-none opacity-80' : ''}`}
          >
            <input {...getInputProps()} />
            <div className="absolute left-1/2 top-full h-40 w-40 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#7c3aed]/20 blur-3xl" />

            {isLoading ? (
              <div className="relative z-10 mx-auto max-w-xl space-y-6">
                <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-[28px] border border-[#8a5cff]/30 bg-[#7c3aed]/10 text-3xl text-[#c5b4ff]">
                  {status === 'uploading' ? '↑' : '⚖'}
                </div>
                <div>
                  <p className="text-xl font-semibold text-white sm:text-2xl">{loadingLabel}</p>
                  <p className="mt-2 text-sm text-slate-400">{fileName || 'Preparing your document for analysis.'}</p>
                </div>

                {status === 'uploading' && (
                  <div className="mx-auto max-w-md">
                    <div className="h-2 rounded-full bg-white/10">
                      <div
                        className="h-2 rounded-full bg-[linear-gradient(90deg,#7c3aed,#f5c26b)] transition-all duration-300"
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                  </div>
                )}

                {analysisLoading && (
                  <div className="flex flex-wrap justify-center gap-2">
                    {['Extracting clauses', 'Scoring risks', 'Preparing summary'].map((step) => (
                      <span key={step} className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-slate-300">
                        {step}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="relative z-10 mx-auto max-w-xl space-y-6">
                <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-[30px] border border-white/10 bg-white/[0.04] text-4xl text-[#8a5cff] shadow-[0_0_40px_rgba(124,58,237,0.2)]">
                  ⤴
                </div>
                <div>
                  <h2 className="text-2xl font-semibold text-white sm:text-3xl">Drag & drop your document here</h2>
                  <p className="mt-3 text-sm leading-7 text-slate-400 sm:text-base">
                    Or click to browse files. PDF, JPG, and PNG supported up to 10MB.
                  </p>
                </div>
                <div className="inline-flex rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-xs uppercase tracking-[0.22em] text-slate-500">
                  PDF . JPG . PNG . Max 10MB
                </div>
              </div>
            )}
          </div>

          {error && (
            <div className="mt-4 rounded-[24px] border border-[#fb7185]/25 bg-[#2a1320]/65 px-5 py-4 text-sm text-[#fecdd3]">
              {error}
            </div>
          )}

          <div className="mt-5 grid gap-3 md:grid-cols-2">
            {documentTypes.map((type) => (
              <div key={type} className="rounded-[20px] border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-slate-300">
                {type}
              </div>
            ))}
          </div>

          <p className="mt-4 text-center text-xs text-slate-500">
            Sign in later if you want saved history and persistent document Q&A.
          </p>
        </div>
      </div>
    </div>
  )
}
