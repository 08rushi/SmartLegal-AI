import { useId, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'

export interface FieldA11y {
  id: string
  'aria-describedby'?: string
  'aria-invalid'?: true
  'aria-required'?: true
}

interface FormFieldProps {
  /** Visible label (always shown above the field; never use placeholder as the only label). */
  label: string
  /** Short help text under the field. */
  hint?: string
  /** Error text; when set, the field is marked invalid and the message is announced. */
  error?: string | null
  required?: boolean
  /** Render the control and spread `a11y` on it:  {(a11y) => <input className="input-field" {...a11y} />} */
  children: (a11y: FieldA11y) => ReactNode
  className?: string
}

/** Label + control + hint + error, wired together (htmlFor/id, aria-describedby, aria-invalid). */
export function FormField({ label, hint, error, required, children, className = '' }: FormFieldProps) {
  const { t } = useTranslation('ui')
  const uid = useId()
  const id = `field-${uid}`
  const hintId = `${id}-hint`
  const errId = `${id}-error`
  const describedBy = [hint ? hintId : null, error ? errId : null].filter(Boolean).join(' ') || undefined
  const a11y: FieldA11y = {
    id,
    'aria-describedby': describedBy,
    'aria-invalid': error ? true : undefined,
    'aria-required': required ? true : undefined,
  }
  return (
    <div className={`space-y-2 ${className}`}>
      <label htmlFor={id} className="block text-sm font-medium text-slate-200">
        {label}
        {required && <span className="ml-1 text-xs font-normal text-slate-400">({t('required')})</span>}
      </label>
      {children(a11y)}
      {hint && (
        <p id={hintId} className="text-xs text-slate-400">
          {hint}
        </p>
      )}
      {error && (
        <p id={errId} role="alert" className="text-sm font-medium text-[#fecdd3]">
          {error}
        </p>
      )}
    </div>
  )
}

export default FormField
