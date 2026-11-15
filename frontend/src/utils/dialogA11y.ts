/**
 * Pure helpers behind accessible dialogs (see hooks/useDialogA11y.ts and components/ui/Modal.tsx).
 * Kept framework-free and "erasable" TypeScript so node can unit-test them.
 */

/** Elements a keyboard user can tab to. */
export const FOCUSABLE_SELECTOR = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled]):not([type="hidden"])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',')

/**
 * Next index when Tab / Shift+Tab is pressed inside a focus trap of `count` focusable items.
 * `current` is the index of the focused item, or -1 when focus is outside the list. Wraps around.
 * Returns -1 when there is nothing focusable (caller should focus the dialog container itself).
 */
export function nextTrapIndex(current: number, count: number, backwards: boolean): number {
  if (count <= 0) return -1
  if (current < 0 || current >= count) return backwards ? count - 1 : 0
  if (backwards) return current === 0 ? count - 1 : current - 1
  return current === count - 1 ? 0 : current + 1
}

// Scroll lock is reference counted so stacked dialogs do not unlock the page too early.
let lockCount = 0
let savedOverflow = ''

interface DocLike {
  body: { style: { overflow: string } }
}

export function lockScroll(doc: DocLike = document): void {
  if (lockCount === 0) {
    savedOverflow = doc.body.style.overflow
    doc.body.style.overflow = 'hidden'
  }
  lockCount += 1
}

export function unlockScroll(doc: DocLike = document): void {
  if (lockCount === 0) return
  lockCount -= 1
  if (lockCount === 0) doc.body.style.overflow = savedOverflow
}

/** Test helper. */
export function _scrollLockCount(): number {
  return lockCount
}

let idCounter = 0
/** Stable-per-call unique id for aria-labelledby / aria-describedby wiring (non-React-18-useId contexts). */
export function nextDomId(prefix: string = 'sl'): string {
  idCounter += 1
  return `${prefix}-${idCounter}`
}
