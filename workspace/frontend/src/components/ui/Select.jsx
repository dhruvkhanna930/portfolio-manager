import { forwardRef } from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '../../utils/cn'

const Select = forwardRef(function Select(
  { label, error, options = [], className, id, ...props },
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
        <select
          ref={ref}
          id={id}
          className={cn(
            'h-10 w-full appearance-none rounded border bg-surface px-3 pr-9 text-sm text-text-primary',
            'border-border focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent',
            error && 'border-negative focus:border-negative focus:ring-negative',
            className
          )}
          {...props}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
      </div>
      {error && <p className="mt-1 text-xs text-negative">{error}</p>}
    </div>
  )
})

export default Select
