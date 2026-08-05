import { useEffect, useRef, useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { ChevronDown } from 'lucide-react'
import { cn } from '../../utils/cn'

const INVESTMENT_LINKS = [
  { to: '/stocks', label: 'Stocks' },
  { to: '/mutual-funds', label: 'Mutual Funds' },
  { to: '/bonds', label: 'Bonds' },
]

export default function InvestmentsDropdown() {
  const [open, setOpen] = useState(false)
  const containerRef = useRef(null)
  const location = useLocation()

  const isActive = INVESTMENT_LINKS.some((link) => location.pathname === link.to)

  useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false)
      }
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
          'flex items-center gap-1 whitespace-nowrap rounded px-3 py-1.5 text-sm font-medium transition-colors duration-150',
          isActive
            ? 'bg-surface text-text-primary'
            : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary'
        )}
      >
        Investments
        <ChevronDown className={cn('h-3.5 w-3.5 transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <div className="absolute left-0 top-full z-50 mt-1 w-44 rounded border border-border bg-surface py-1 shadow-lg">
          {INVESTMENT_LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              onClick={() => setOpen(false)}
              className={({ isActive: linkActive }) =>
                cn(
                  'block px-3 py-2 text-sm font-medium transition-colors duration-150',
                  linkActive
                    ? 'bg-surface-hover text-text-primary'
                    : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary'
                )
              }
            >
              {link.label}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  )
}
