import { useCallback, useEffect, useMemo, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { analyzeDocument } from '../store/analysisSlice'
import { clearDocumentError, uploadDocument } from '../store/documentSlice'
import { trackEvent } from '../utils/posthog'

const documentTypes = [
  'Rental Agreement',
  'Employment Contract',
  'Loan Agreement',
  'Service Contract',
]

const steps = ['Upload', 'Preview', 'Analyze', 'Results']

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function UploadSkeleton({ status, uploadProgress, fileName }: { status: string; uploadProgress: number; fileName: string }) {
  const isUploading = status === 'uploading'
  const title = isUploading ? `Uploading... ${uploadProgress}%` : 'Analyzing your document...'
  const subtitle = isUploading
    ? 'We are securely storing your file and preparing it for review.'
    : 'AI is reading every clause and building a structured overview for you.'

  return (
    <div className="relative z-10 mx-auto max-w-xl space-y-6">
      <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-[28px] border border-[#8a5cff]/30 bg-[#7c3aed]/10 text-3xl text-[#c5b4ff] shadow-[0_0_40px_rgba(124,58,237,0.16)]">
        {isUploading ? '↑' : '⚖'}
      </div>

      <div className="space-y-3 text-center">
        <div>
          <p className="text-xl font-semibold text-white sm:text-2xl">{title}</p>
          <p className="mx-auto mt-2 max-w-lg text-sm leading-7 text-slate-400">{subtitle}</p>
        </div>
        <div className="flex flex-wrap justify-center gap-2">
          {['Extracting pages', 'Scoring risks', 'Preparing summary'].map((step) => (
            <span key={step} className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-slate-300">
              {step}
            </span>
          ))}
        </div>
      </div>

      {fileName ? (
        <div className="rounded-[24px] border border-white/10 bg-white/[0.03] px-4 py-4 text-left">
          <p className="truncate text-sm font-medium text-white">{fileName}</p>
          <p className="mt-1 text-xs text-slate-400">
            {isUploading ? `Uploading ${uploadProgress}%` : 'Preparing analysis workspace'}
          </p>
        </div>
      ) : null}

      <div className="space-y-3">
        <div className="h-2 rounded-full bg-white/10">
          <div
            className="h-2 rounded-full bg-[linear-gradient(90deg,#7c3aed,#f5c26b)] transition-all duration-300"
            style={{ width: `${isUploading ? uploadProgress : 100}%` }}
          />
        </div>
        <div className="grid gap-3">
          {[1, 2, 3].map((item) => (
            <div key={item} className="skeleton-block h-14 w-full rounded-[20px]" />
          ))}
        </div>
      </div>
    </div>
  )
}

export default function Upload() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { status, uploadProgress, error } = useAppSelector((s) => s.document)
  const analysisLoading = useAppSelector((s) => s.analysis.isLoading)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  useEffect(() => {
    dispatch(clearDocumentError())
  }, [dispatch])

  useEffect(() => {
    if (!selectedFile) {
      setPreviewUrl(null)
      return
    }

    const nextUrl = URL.createObjectURL(selectedFile)
    setPreviewUrl(nextUrl)

    return () => {
      URL.revokeObjectURL(nextUrl)
    }
  }, [selectedFile])

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    setSelectedFile(file)
    trackEvent('document_preview_selected', {
      fileName: file.name,
      mimeType: file.type || 'unknown',
      fileSize: file.size,
    })
  }, [])

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
    noClick: true,
    disabled: status === 'uploading' || analysisLoading,
  })

  const isLoading = status === 'uploading' || analysisLoading
  const isImagePreview = selectedFile?.type.startsWith('image/')
  const isPdfPreview = selectedFile?.type === 'application/pdf'
  const fileExtension = useMemo(() => selectedFile?.name.split('.').pop()?.toUpperCase() || 'FILE', [selectedFile])

  async function handleAnalyze() {
    if (!selectedFile) return

    trackEvent('document_upload_started', {
      fileName: selectedFile.name,
      mimeType: selectedFile.type || 'unknown',
      fileSize: selectedFile.size,
    })

    const uploadResult = await dispatch(uploadDocument(selectedFile))
    if (uploadDocument.rejected.match(uploadResult)) {
      trackEvent('document_upload_failed', {
        fileName: selectedFile.name,
      })
      return
    }

    const doc = uploadResult.payload as { id: string }
    trackEvent('document_upload_completed', { documentId: doc.id })

    const analyzeResult = await dispatch(analyzeDocument(doc.id))
    if (analyzeDocument.fulfilled.match(analyzeResult)) {
      trackEvent('analysis_requested', { documentId: doc.id })
      navigate(`/analysis/${doc.id}`)
    }
  }

  function handleClearSelection() {
    setSelectedFile(null)
    dispatch(clearDocumentError())
  }

  return (
    <div className="content-wrap py-8 sm:py-10">
      <div className="mx-auto grid max-w-7xl gap-6 xl:grid-cols-[0.86fr_1.14fr]">
        <div className="section-card rounded-[32px] p-6 sm:p-8">
          <span className="section-eyebrow">03 Upload Document</span>
          <h1 className="mt-4 text-3xl font-semibold text-white sm:text-4xl">Upload Your PDF Document</h1>
          <p className="mt-3 text-sm leading-7 text-slate-400 sm:text-base">
            Drop a PDF contract, preview it first, then run analysis when you are sure it is the right file.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            {steps.map((step, index) => (
              <div key={step} className="flex items-center gap-3">
                <div className={`flex h-10 min-w-10 items-center justify-center rounded-full border px-3 text-xs font-semibold ${
                  index <= (selectedFile ? 1 : 0)
                    ? 'border-[#8a5cff]/40 bg-[#8a5cff]/15 text-[#c5b4ff]'
                    : 'border-white/10 bg-white/[0.03] text-slate-500'
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
            className={`upload-dropzone relative overflow-hidden rounded-[30px] border border-dashed px-5 py-8 text-center transition-all duration-300 sm:px-8 sm:py-10 ${
              isDragActive
                ? 'border-[#f5c26b]/55 bg-[#15101d]/80 shadow-[0_0_40px_rgba(245,194,107,0.16)]'
                : 'border-white/12 bg-[#0b1120]/72 hover:border-[#8a5cff]/35 hover:bg-[#10172a]/80'
            } ${isLoading ? 'pointer-events-none opacity-80' : ''}`}
          >
            <input {...getInputProps()} />
            <div className="absolute left-1/2 top-full h-40 w-40 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#7c3aed]/20 blur-3xl" />

            {isLoading ? (
              <UploadSkeleton
                status={status}
                uploadProgress={uploadProgress}
                fileName={selectedFile?.name || ''}
              />
            ) : selectedFile ? (
              <div className="relative z-10 mx-auto max-w-2xl space-y-6 text-left">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-[0.22em] text-slate-500">File Preview</p>
                    <h2 className="mt-2 text-2xl font-semibold text-white sm:text-3xl">{selectedFile.name}</h2>
                    <p className="mt-3 text-sm leading-7 text-slate-400">
                      Review the file details below, then start analysis when you are ready.
                    </p>
                  </div>
                  <div className="inline-flex rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-xs uppercase tracking-[0.22em] text-slate-400">
                    {fileExtension} • {formatSize(selectedFile.size)}
                  </div>
                </div>

                <div className="grid items-start gap-4 lg:grid-cols-[1.2fr_0.8fr]">
                  <div className="info-card self-start overflow-hidden rounded-[24px] p-3">
                    {isImagePreview && previewUrl ? (
                      <img
                        src={previewUrl}
                        alt={selectedFile.name}
                        className="aspect-[4/5] w-full rounded-[18px] object-contain bg-[#050913] sm:aspect-[3/4]"
                      />
                    ) : isPdfPreview && previewUrl ? (
                      <iframe
                        title={`${selectedFile.name} preview`}
                        src={previewUrl}
                        className="aspect-[4/5] w-full rounded-[18px] border border-white/10 bg-white sm:aspect-[3/4]"
                      />
                    ) : (
                      <div className="flex aspect-[4/5] w-full flex-col items-center justify-center rounded-[18px] border border-white/10 bg-white/[0.03] text-center sm:aspect-[3/4]">
                        <div className="rounded-[24px] border border-white/10 bg-white/[0.04] px-6 py-5 text-4xl text-[#8a5cff]">
                          {fileExtension}
                        </div>
                        <p className="mt-4 text-lg font-medium text-white">{selectedFile.name}</p>
                        <p className="mt-2 max-w-sm text-sm text-slate-400">
                          This PDF file is ready to analyze. You can proceed to document analysis.
                        </p>
                      </div>
                    )}
                  </div>

                  <div className="space-y-4">
                    <div className="info-card rounded-[24px] p-5">
                      <p className="text-sm font-medium text-white">Selected File</p>
                      <div className="mt-4 space-y-3 text-sm text-slate-300">
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-slate-500">Name</span>
                          <span className="max-w-[180px] truncate text-right">{selectedFile.name}</span>
                        </div>
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-slate-500">Type</span>
                          <span>{selectedFile.type || 'Unknown'}</span>
                        </div>
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-slate-500">Size</span>
                          <span>{formatSize(selectedFile.size)}</span>
                        </div>
                      </div>
                    </div>

                    <div className="rounded-[24px] border border-[#f5c26b]/16 bg-[#1b1720]/80 p-5">
                      <p className="text-sm font-medium text-[#f5c26b]">Before you analyze</p>
                      <ul className="mt-3 space-y-2 text-sm leading-7 text-slate-300">
                        <li>• Confirm this is the exact document version you want reviewed.</li>
                        <li>• Text-based PDF files are supported up to 10MB.</li>
                        <li>• Analysis can take up to a couple of minutes for long contracts.</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col gap-3 sm:flex-row">
                  <button type="button" onClick={handleAnalyze} className="btn-primary" disabled={isLoading}>
                    Analyze Document
                  </button>
                  <button type="button" onClick={open} className="btn-secondary">
                    Replace File
                  </button>
                  <button type="button" onClick={handleClearSelection} className="btn-secondary">
                    Remove
                  </button>
                </div>
              </div>
            ) : (
              <div className="relative z-10 mx-auto max-w-xl space-y-6">
                <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-[30px] border border-white/10 bg-white/[0.04] text-4xl text-[#8a5cff] shadow-[0_0_40px_rgba(124,58,237,0.2)]">
                  ⇪
                </div>
                <div>
                  <h2 className="text-2xl font-semibold text-white sm:text-3xl">Drag & drop your document here</h2>
                  <p className="mt-3 text-sm leading-7 text-slate-400 sm:text-base">
                    Choose a file first, preview it, then run AI analysis when you are ready.
                  </p>
                </div>
                <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
                  <button type="button" onClick={open} className="btn-primary">
                    Browse Files
                  </button>
                  <div className="inline-flex rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-xs uppercase tracking-[0.22em] text-slate-500">
                    PDF only . Max 10MB
                  </div>
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
