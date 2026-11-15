interface SkeletonProps {
  className?: string
}

/** Placeholder block while content loads. Decorative (hidden from screen readers); pair with a Spinner/status text. */
export function Skeleton({ className = 'h-4 w-full' }: SkeletonProps) {
  return <div aria-hidden="true" className={`skeleton-block rounded-xl ${className}`} />
}

export default Skeleton
