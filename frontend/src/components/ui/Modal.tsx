import { useId, useRef, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { useDialogA11y } from '../../hooks/useDialogA11y'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  /** Visible heading (rendered in the header row and used as the dialog's accessible name). */
  title?: string
  /**
   * Use instead of `title` when the children contain their own heading: pass that heading's id and the dialog
   * is labelled by it. One of `title` / `labelledBy` / `ariaLabel` is required for an accessible name.
   */
  labelledBy?: string
  ariaLabel?: string
  /** Kept for compatibility: both values render the same centred card. */
  variant?: 'dialog' | 'sheet'
  size?: 'sm' | 'md' | 'lg' | 'xl'
  /** `card` = the Home practice-area look (section card, ✕ in the corner, children bring their own heading). */
  look?: 'modal' | 'card'
  /** Click on the dark backdrop closes the dialog. Default true; set false while busy. */
  closeOnBackdrop?: boolean
  /** Hide the built-in Close button (only if the content provides its own way out). */
  hideClose?: boolean
  children: ReactNode
}

const SIZE = { sm: 'max-w-md', md: 'max-w-2xl', lg: 'max-w-3xl', xl: 'max-w-4xl' } as const

/**
 * Modal with the original look (dark card, title row, ✕). Accessible: role="dialog" aria-modal, labelled,
 * focus trap, Escape closes, initial focus, focus returns to the opener, page scroll locked.
 */
export function Modal({
  isOpen,
  onClose,
  title,
  labelledBy,
  ariaLabel,
  size = 'md',
  look = 'modal',
  closeOnBackdrop = true,
  hideClose = false,
  children,
}: ModalProps) {
  const { t } = useTranslation('ui')
  const panelRef = useRef<HTMLDivElement>(null)
  const autoId = useId()
  const titleId = `modal-title-${autoId}`
  useDialogA11y({ open: isOpen, onClose, containerRef: panelRef })

  if (!isOpen) return null

  const card = look === 'card'
  const closeLabel = t('close')
  return (
    <div
      className={
        card
          ? 'fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-md animate-fadeIn'
          : 'fixed inset-0 z-[60] flex items-center justify-center overflow-y-auto bg-black/80 p-4 backdrop-blur-sm animate-fadeIn'
      }
      onMouseDown={(e) => {
        if (closeOnBackdrop && e.target === e.currentTarget) onClose()
      }}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? titleId : labelledBy}
        aria-label={title || labelledBy ? undefined : ariaLabel}
        tabIndex={-1}
        className={
          card
            ? `section-card relative max-h-[90vh] w-full overflow-y-auto rounded-[32px] p-6 outline-none sm:p-8 ${SIZE[size]}`
            : `relative max-h-[90vh] w-full space-y-6 overflow-y-auto rounded-3xl border border-slate-700/80 bg-[#121a2d] p-6 shadow-2xl outline-none sm:p-8 ${SIZE[size]}`
        }
      >
        {card ? (
          !hideClose && (
            <button
              type="button"
              onClick={onClose}
              aria-label={closeLabel}
              title={closeLabel}
              className="absolute right-6 top-6 flex h-8 w-8 items-center justify-center rounded-full border border-white/10 bg-white/5 text-slate-400 hover:text-white"
            >
              <span aria-hidden="true">✕</span>
            </button>
          )
        ) : (
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            {title && (
              <h3 id={titleId} className="text-xl font-bold text-white">
                {title}
              </h3>
            )}
            {!hideClose && (
              <button
                type="button"
                onClick={onClose}
                aria-label={closeLabel}
                title={closeLabel}
                className="ml-auto flex h-8 w-8 items-center justify-center rounded-full bg-slate-800/80 text-lg font-bold text-slate-400 hover:text-white"
              >
                <span aria-hidden="true">✕</span>
              </button>
            )}
          </div>
        )}
        <div>{children}</div>
      </div>
    </div>
  )
}

export default Modal
