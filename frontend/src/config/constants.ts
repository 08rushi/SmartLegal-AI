/**
 * Shared Application Constants & Token Configs (SL-039).
 */

export const APP_NAME = 'SmartLegal AI'

export const RISK_CONFIG = {
  high: {
    label: 'High Risk',
    color: 'text-rose-400',
    bg: 'bg-rose-500/10',
    border: 'border-rose-500/20',
  },
  medium: {
    label: 'Medium Risk',
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/20',
  },
  low: {
    label: 'Low Risk',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/20',
  },
}

export const SUPPORTED_FILE_TYPES = [
  'application/pdf',
  'image/jpeg',
  'image/png',
  'image/webp',
]

export const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024 // 10 MB
