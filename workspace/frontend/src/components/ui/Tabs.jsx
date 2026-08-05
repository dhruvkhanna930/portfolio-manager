import { cn } from '../../utils/cn'

export default function Tabs({ tabs, value, onChange, className }) {
  return (
    <div
      role="tablist"
      className={cn(
        'inline-flex items-center gap-1 rounded border border-border bg-surface p-1',
        className
      )}
    >
      {tabs.map((tab) => {
        const active = tab.key === value
        return (
          <button
            key={tab.key}
            role="tab"
            aria-selected={active}
            onClick={() => onChange?.(tab.key)}
            className={cn(
              'rounded px-3 py-1.5 text-sm font-medium transition-colors duration-150',
              active
                ? 'bg-accent text-bg'
                : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary'
            )}
          >
            {tab.label}
          </button>
        )
      })}
    </div>
  )
}
