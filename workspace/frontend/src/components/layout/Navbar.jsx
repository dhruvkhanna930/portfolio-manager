import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { Menu, Wallet, X } from 'lucide-react'
import { cn } from '../../utils/cn'
import NavbarSearch from './NavbarSearch'
import InvestmentsDropdown from './InvestmentsDropdown'

const NAV_LINKS = [
  { to: '/', label: 'Home' },
  { to: '/portfolio', label: 'My Portfolio' },
  { to: '/transactions', label: 'Transactions' },
  { to: '/sips', label: 'SIPs' },
  { to: '/news', label: 'News' },
  { to: '/calculators', label: 'Calculators' },
]

const INVESTMENT_LINKS = [
  { to: '/stocks', label: 'Stocks' },
  { to: '/mutual-funds', label: 'Mutual Funds' },
  { to: '/bonds', label: 'Bonds' },
]

const linkClass = ({ isActive }) =>
  cn(
    'whitespace-nowrap rounded px-3 py-1.5 text-sm font-medium transition-colors duration-150',
    isActive
      ? 'bg-surface text-text-primary'
      : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary'
  )

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-bg/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 sm:px-6">
        <div className="flex shrink-0 items-center gap-2 text-text-primary">
          <Wallet className="h-5 w-5 shrink-0 text-accent" />
          <span className="hidden text-sm font-semibold tracking-wide sm:inline">
            Portfolio Manager
          </span>
        </div>

        {/* Desktop nav: hidden below lg, where it would otherwise wrap/overflow */}
        <nav className="hidden min-w-0 items-center gap-1 lg:flex">
          <NavLink to="/" end className={linkClass}>
            Home
          </NavLink>
          <NavLink to="/portfolio" className={linkClass}>
            My Portfolio
          </NavLink>
          <NavLink to="/transactions" className={linkClass}>
            Transactions
          </NavLink>
          <InvestmentsDropdown />
          <NavLink to="/sips" className={linkClass}>
            SIPs
          </NavLink>
          <NavLink to="/news" className={linkClass}>
            News
          </NavLink>
          <NavLink to="/calculators" className={linkClass}>
            Calculators
          </NavLink>
        </nav>

        <div className="ml-auto flex shrink-0 items-center gap-2">
          <div className="hidden sm:block">
            <NavbarSearch />
          </div>
          <button
            type="button"
            onClick={() => setMobileOpen((v) => !v)}
            className="rounded p-2 text-text-secondary hover:bg-surface-hover hover:text-text-primary lg:hidden"
            aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="border-t border-border px-4 pb-4 pt-3 lg:hidden">
          <div className="mb-3 sm:hidden">
            <NavbarSearch />
          </div>
          <nav className="flex flex-col gap-1">
            {NAV_LINKS.slice(0, 3).map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.to === '/'}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  cn(
                    'rounded px-3 py-2 text-sm font-medium transition-colors duration-150',
                    isActive
                      ? 'bg-surface text-text-primary'
                      : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary'
                  )
                }
              >
                {link.label}
              </NavLink>
            ))}

            <p className="mt-2 px-3 text-xs font-medium uppercase tracking-wide text-text-muted">
              Investments
            </p>
            {INVESTMENT_LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  cn(
                    'rounded px-3 py-2 text-sm font-medium transition-colors duration-150',
                    isActive
                      ? 'bg-surface text-text-primary'
                      : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary'
                  )
                }
              >
                {link.label}
              </NavLink>
            ))}

            <div className="mt-2 border-t border-border pt-2" />
            {NAV_LINKS.slice(3).map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  cn(
                    'rounded px-3 py-2 text-sm font-medium transition-colors duration-150',
                    isActive
                      ? 'bg-surface text-text-primary'
                      : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary'
                  )
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>
        </div>
      )}
    </header>
  )
}
