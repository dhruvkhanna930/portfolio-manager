import { cn } from '../../utils/cn'

const TONE_CLASSES = {
  positive: 'bg-positive-soft text-positive',
  negative: 'bg-negative-soft text-negative',
  neutral: 'bg-surface-hover text-text-secondary',
  warning: 'bg-warning-soft text-warning',
  accent: 'bg-accent-soft text-accent',
}

export default function Badge({ tone = 'neutral', children, className }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium tabular-nums',
        TONE_CLASSES[tone],
        className
      )}
    >
      {children}
    </span>
  )
}
