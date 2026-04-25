import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { uploadDocument } from '../store/documentSlice'
import { analyzeDocument } from '../store/analysisSlice'

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

      // 1. Upload the file
      const uploadResult = await dispatch(uploadDocument(file))
      if (uploadDocument.rejected.match(uploadResult)) return

      const doc = uploadResult.payload as { id: string }

      // 2. Immediately trigger AI analysis
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
    <div className="min-h-screen bg-gray-50 py-16 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-gray-900 mb-3">Upload your document</h1>
          <p className="text-gray-500">
            Supports rental agreements, employment contracts, loan papers, and any legal PDF.
          </p>
        </div>

        {/* Drop zone */}
        <div
          {...getRootProps()}
          className={`relative border-2 border-dashed rounded-2xl p-16 text-center cursor-pointer transition-all duration-200
            ${isDragActive ? 'border-brand-500 bg-brand-50 scale-[1.01]' : 'border-gray-300 bg-white hover:border-brand-400 hover:bg-gray-50'}
            ${isLoading ? 'pointer-events-none opacity-70' : ''}
          `}
        >
          <input {...getInputProps()} />

          {isLoading ? (
            <div className="space-y-4">
              <div className="text-4xl animate-bounce">
                {status === 'uploading' ? '📤' : '🤖'}
              </div>
              <p className="text-lg font-semibold text-brand-600">{loadingLabel}</p>

              {status === 'uploading' && (
                <div className="w-full bg-gray-200 rounded-full h-2 max-w-xs mx-auto">
                  <div
                    className="bg-brand-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              )}

              {analysisLoading && (
                <div className="flex justify-center gap-1 mt-2">
                  {['Extracting clauses', 'Scoring risks', 'Translating to Hindi'].map((step, i) => (
                    <span
                      key={step}
                      className="text-xs bg-brand-100 text-brand-700 px-2 py-1 rounded-full animate-pulse"
                      style={{ animationDelay: `${i * 0.3}s` }}
                    >
                      {step}
                    </span>
                  ))}
                </div>
              )}

              {fileName && (
                <p className="text-sm text-gray-400 mt-2">📄 {fileName}</p>
              )}
            </div>
          ) : isDragActive ? (
            <div className="space-y-3">
              <div className="text-5xl">📂</div>
              <p className="text-xl font-semibold text-brand-600">Drop it here!</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-5xl">📄</div>
              <div>
                <p className="text-lg font-semibold text-gray-700">
                  Drag & drop your document here
                </p>
                <p className="text-gray-400 text-sm mt-1">or click to browse files</p>
              </div>
              <p className="text-xs text-gray-400">PDF, JPG, PNG • Max 10MB</p>
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
            ⚠️ {error}
          </div>
        )}

        {/* Supported document types */}
        <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { icon: '🏠', label: 'Rental Agreement' },
            { icon: '💼', label: 'Employment Contract' },
            { icon: '💰', label: 'Loan Agreement' },
            { icon: '🤝', label: 'Freelance Contract' },
          ].map((type) => (
            <div
              key={type.label}
              className="bg-white border border-gray-200 rounded-xl p-3 text-center text-sm text-gray-600"
            >
              <div className="text-xl mb-1">{type.icon}</div>
              {type.label}
            </div>
          ))}
        </div>

        {/* Note about auth */}
        <p className="text-center text-xs text-gray-400 mt-6">
          💡 Sign in to save your document history and access Q&A chat
        </p>
      </div>
    </div>
  )
}
