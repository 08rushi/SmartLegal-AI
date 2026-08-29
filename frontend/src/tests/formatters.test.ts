import { describe, it, expect } from 'vitest'
import { formatFileSize, formatDate, sanitizeErrorMessage } from '../utils/formatters'

describe('Formatting Utilities (SL-047)', () => {
  it('formats file sizes in bytes, KB, MB cleanly', () => {
    expect(formatFileSize(0)).toBe('0 B')
    expect(formatFileSize(1024)).toBe('1 KB')
    expect(formatFileSize(1048576)).toBe('1 MB')
    expect(formatFileSize(5242880)).toBe('5 MB')
  })

  it('formats ISO dates accurately', () => {
    expect(formatDate(null)).toBe('N/A')
    expect(formatDate(undefined)).toBe('N/A')
    const formatted = formatDate('2026-08-29T12:00:00Z')
    expect(formatted).toContain('2026')
  })

  it('sanitizes API error objects and strings', () => {
    expect(sanitizeErrorMessage('Direct error message')).toBe('Direct error message')
    expect(
      sanitizeErrorMessage({ response: { data: { detail: 'API Bad Request' } } })
    ).toBe('API Bad Request')
  })
})
