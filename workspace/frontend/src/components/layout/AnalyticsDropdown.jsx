import { useEffect, useRef, useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { ChevronDown } from 'lucide-react'
import { cn } from '../../utils/cn'

/**
 * Analytics menu.
 *
 * All three entries are built as of Phase 17. The disabled-row branch below is
 * kept deliberately: it renders any future entry with `to: null` as an explicit
 * "Soon" row rather than a link to an empty page, since a menu item that
 * navigates somewhere blank reads as a broken feature.
 */
export const ANALYTICS_LINKS = [
  { to: '/analytics', label: 'Advanced Analytics', hint: 'Risk, correlation, projections' },
  {
    to: '/recommendations',
    label: 'Recommendation Model',
    hint: 'Ranked candidates with score breakdown',
  },
  {
    to: '/ai-suggestions',
    label: 'AI Suggestions',
    hint: 'Plain-English review of your numbers',
  },
]

export default function AnalyticsDropdown() {
  const [open, setOpen] = useState(false)
  const containerRef = useRef(null)
  const location = useLocation()

  const isActive = ANALYTICS_LINKS.some((link) => link.to && location.pathname === link.to)

  useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false)
    }
    function handleEscape(e) {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [])

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className={cn(
          'flex items-center gap-1 whitespace-nowrap rounded px-2 py-1.5 text-sm font-medium transition-colors duration-150 xl:px-3',
          isActive
            ? 'bg-surface text-text-primary'
            : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary'
        )}
      >
        Analytics
        <ChevronDown className={cn('h-3.5 w-3.5 transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <div className="absolute left-0 top-full z-50 mt-1 w-60 rounded border border-border bg-surface py-1 shadow-lg">
          {ANALYTICS_LINKS.map((link) =>
            link.to ? (
              <NavLink
                key={link.label}
                to={link.to}
                onClick={() => setOpen(false)}
                className={({ isActive: linkActive }) =>
                  cn(
                    'block px-3 py-2 transition-colors duration-150',
                    linkActive
                      ? 'bg-surface-hover text-text-primary'
                      : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary'
                  )
                }
              >
                <span className="block text-sm font-medium">{link.label}</span>
                <span className="block text-xs text-text-muted">{link.hint}</span>
              </NavLink>
            ) : (
              <div
                key={link.label}
                aria-disabled="true"
                title="Not built yet"
                className="cursor-not-allowed px-3 py-2 opacity-55"
              >
                <span className="flex items-center gap-2 text-sm font-medium text-text-secondary">
                  {link.label}
                  <span className="rounded-full bg-surface-hover px-1.5 py-0.5 text-[10px] font-medium text-text-muted">
                    Soon
                  </span>
                </span>
                <span className="block text-xs text-text-muted">{link.hint}</span>
              </div>
            )
          )}
        </div>
      )}
    </div>
  )
}
