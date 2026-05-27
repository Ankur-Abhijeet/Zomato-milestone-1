import './ui.css'

// ── Spinner ───────────────────────────────────────────────────────────────────

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'accent'
  className?: string
}

export function Spinner({ size = 'md', variant = 'default', className = '' }: SpinnerProps) {
  const cls = [
    'spinner',
    size === 'sm' ? 'spinner--sm' : size === 'lg' ? 'spinner--lg' : '',
    variant === 'accent' ? 'spinner--accent' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')
  return <span className={cls} role="status" aria-label="Loading…" />
}

// ── Toast ─────────────────────────────────────────────────────────────────────

export type ToastVariant = 'error' | 'warning' | 'info' | 'success'

export interface ToastItem {
  id: string
  variant: ToastVariant
  title: string
  message: string
}

const ICONS: Record<ToastVariant, string> = {
  error:   '🔴',
  warning: '⚠️',
  info:    'ℹ️',
  success: '🟢',
}

interface ToastProps {
  items: ToastItem[]
  onDismiss: (id: string) => void
}

export function Toast({ items, onDismiss }: ToastProps) {
  if (!items.length) return null
  return (
    <div className="toast-container" role="region" aria-label="Notifications">
      {items.map((item) => (
        <div key={item.id} className={`toast toast--${item.variant}`} role="alert">
          <span className="toast__icon">{ICONS[item.variant]}</span>
          <div className="toast__body">
            <div className="toast__title">{item.title}</div>
            <div className="toast__message">{item.message}</div>
          </div>
          <button
            className="toast__close"
            onClick={() => onDismiss(item.id)}
            aria-label="Dismiss notification"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  )
}

// ── Skeleton Card ──────────────────────────────────────────────────────────────

export function SkeletonCard() {
  return (
    <div className="skeleton-card" aria-hidden="true">
      <div className="skeleton-card__header">
        <div className="skeleton skeleton-card__badge" />
        <div className="skeleton-card__title-block">
          <div className="skeleton skeleton-card__line skeleton-card__line--wide" />
          <div className="skeleton skeleton-card__line skeleton-card__line--mid" />
        </div>
      </div>
      <div className="skeleton skeleton-card__line skeleton-card__line--short" />
      <div className="skeleton skeleton-card__line skeleton-card__line--full skeleton-card__line--body" />
      <div className="skeleton skeleton-card__line skeleton-card__line--full skeleton-card__line--body" />
      <div className="skeleton skeleton-card__line skeleton-card__line--mid skeleton-card__line--body" />
    </div>
  )
}
