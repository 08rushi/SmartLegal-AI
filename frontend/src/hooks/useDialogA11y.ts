import { useEffect, useRef, type RefObject } from 'react'
import { FOCUSABLE_SELECTOR, lockScroll, nextTrapIndex, unlockScroll } from '../utils/dialogA11y'

interface Options {
  open: boolean
  onClose: () => void
  /** The dialog panel (should have role="dialog" aria-modal="true" and tabIndex={-1}). */
  containerRef: RefObject<HTMLElement>
  /** Element to focus first. Defaults to the first focusable element, else the panel itself. */
  initialFocusRef?: RefObject<HTMLElement>
}

/**
 * Dialog behaviour: initial focus, focus trap (Tab / Shift+Tab wrap), Escape to close, page scroll lock,
 * and restoring focus to whatever was focused before opening. Used by ui/Modal; use Modal instead of calling
 * this directly unless you build a custom overlay.
 */
export function useDialogA11y({ open, onClose, containerRef, initialFocusRef }: Options) {
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  useEffect(() => {
    if (!open) return
    const container = containerRef.current
    if (!container) return
    const previous = document.activeElement as HTMLElement | null

    lockScroll()

    const focusables = () =>
      Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)).filter(
        (el) => el.offsetParent !== null || el === document.activeElement,
      )

    const first = initialFocusRef?.current ?? focusables()[0] ?? container
    first.focus()

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation()
        e.preventDefault()
        onCloseRef.current()
        return
      }
      if (e.key !== 'Tab') return
      const items = focusables()
      const idx = items.indexOf(document.activeElement as HTMLElement)
      const next = nextTrapIndex(idx, items.length, e.shiftKey)
      if (next === -1) {
        e.preventDefault()
        container.focus()
      } else if (idx === -1 || (e.shiftKey && idx === 0) || (!e.shiftKey && idx === items.length - 1)) {
        e.preventDefault()
        items[next].focus()
      }
    }
    container.addEventListener('keydown', onKeyDown)

    return () => {
      container.removeEventListener('keydown', onKeyDown)
      unlockScroll()
      if (previous && document.contains(previous)) previous.focus()
    }
  }, [open, containerRef, initialFocusRef])
}
