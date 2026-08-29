/**
 * Shared Formatting Helpers (SL-039).
 */

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

export function formatDate(isoString: string | null | undefined): string {
  if (!isoString) return 'N/A'
  try {
    const d = new Date(isoString)
    return d.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })
  } catch {
    return isoString
  }
}

export function formatRelativeTime(isoString: string): string {
  if (!isoString) return 'recently'
  try {
    const date = new Date(isoString)
    const now = new Date()
    const diffSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (diffSeconds < 60) return 'just now'
    if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`
    if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)}h ago`
    return `${Math.floor(diffSeconds / 86400)}d ago`
  } catch {
    return 'recently'
  }
}

export function sanitizeErrorMessage(err: unknown): string {
  if (typeof err === 'string') return err
  if (err && typeof err === 'object') {
    const e = err as { response?: { data?: { detail?: string } }; message?: string }
    if (e.response?.data?.detail) return e.response.data.detail
    if (e.message) return e.message
  }
  return 'An unexpected error occurred. Please try again.'
}
