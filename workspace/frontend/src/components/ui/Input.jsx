import { forwardRef } from 'react'
import { cn } from '../../utils/cn'

const Input = forwardRef(function Input(
  { label, error, icon: Icon, className, id, ...props },
  ref
) {
  return (
    <div className="w-full">
      {label && (
        <label htmlFor={id} className="mb-1.5 block text-sm text-text-secondary">
          {label}
        </label>
      )}
      <div className="relative">
        {Icon && (
          <Icon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
        )}
        <input
          ref={ref}
          id={id}
          className={cn(
            'h-10 w-full rounded border bg-surface px-3 text-sm text-text-primary placeholder:text-text-muted',
            'border-border focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent',
            Icon && 'pl-9',
            error && 'border-negative focus:border-negative focus:ring-negative',
            className
          )}
          {...props}
        />
      </div>
      {error && <p className="mt-1 text-xs text-negative">{error}</p>}
    </div>
  )
})

export default Input
