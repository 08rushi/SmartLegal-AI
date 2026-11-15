import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react'
import { Link, type LinkProps } from 'react-router-dom'
import { Icon, type IconName } from './Icon'
import { Spinner } from './Spinner'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost'

interface CommonProps {
  variant?: ButtonVariant
  /** `lg` (default, roomier) or `md` (the standard glass button size). */
  size?: 'lg' | 'md'
  /** Stretch to full width. */
  block?: boolean
  /** Optional leading icon (always paired with the text children). */
  icon?: IconName
  children: ReactNode
}

export type ButtonProps = CommonProps & ButtonHTMLAttributes<HTMLButtonElement> & { loading?: boolean }
export type ButtonLinkProps = CommonProps & Omit<LinkProps, 'children'>;

const VARIANT: Record<ButtonVariant, string> = {
  primary: 'btn-primary',
  secondary: 'btn-secondary',
  ghost: 'btn-ghost',
}

function cls(variant: ButtonVariant, size: 'lg' | 'md', block: boolean, extra?: string) {
  return [VARIANT[variant], size === 'lg' ? 'px-6 py-3.5 text-base' : '', block ? 'w-full' : '', extra ?? '']
    .filter(Boolean)
    .join(' ')
}

/** Glass-theme <button type="button">. `loading` disables it and shows a spinner. */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'primary', size = 'lg', block = false, icon, loading = false, disabled, type = 'button', className, children, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={cls(variant, size, block, className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? <Spinner size={20} /> : icon && <Icon name={icon} size={20} />}
      <span>{children}</span>
    </button>
  )
})

/** Router <Link> that looks like a Button. Use for navigation. */
export function ButtonLink({ variant = 'primary', size = 'lg', block = false, icon, className, children, ...rest }: ButtonLinkProps) {
  return (
    <Link className={cls(variant, size, block, className)} {...rest}>
      {icon && <Icon name={icon} size={20} />}
      <span>{children}</span>
    </Link>
  )
}

export default Button
