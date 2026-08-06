import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { Menu, Search, Wallet, X } from 'lucide-react'
import { cn } from '../../utils/cn'
import AlertsBell from './AlertsBell'
import NavbarSearch from './NavbarSearch'
import AnalyticsDropdown, { ANALYTICS_LINKS } from './AnalyticsDropdown'
import InvestmentsDropdown from './InvestmentsDropdown'

// The wordmark on the left also links home; this is the explicit entry beside it.
const PRIMARY_LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/portfolio', label: 'My Portfolio' },
  { to: '/transactions', label: 'Transactions' },
]

// Goals lives inside Analytics (Projections tab), so it isn't duplicated here.
const SECONDARY_LINKS = [
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
    'whitespace-nowrap rounded px-2 py-1.5 text-sm font-medium transition-colors duration-150 xl:px-3',
    isActive
      ? 'bg-surface text-text-primary'
      : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary'
  )

const mobileLinkClass = ({ isActive }) =>
  cn(
    'rounded px-3 py-2 text-sm font-medium transition-colors duration-150',
    isActive
      ? 'bg-surface text-text-primary'
      : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary'
  )

function MobileGroupLabel({ children }) {
  return (
    <p className="mt-2 px-3 text-xs font-medium uppercase tracking-wide text-text-muted">
      {children}
    </p>
  )
}

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const close = () => setMobileOpen(false)

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-bg/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 sm:px-6">
        <Link
          to="/"
          onClick={close}
          aria-label="Portfolio Manager — go to home"
          className="flex shrink-0 items-center gap-2 rounded text-text-primary transition-colors hover:text-accent focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        >
          <Wallet className="h-5 w-5 shrink-0 text-accent" />
          <span className="hidden text-sm font-semibold tracking-wide sm:inline">
            Portfolio Manager
          </span>
        </Link>

        {/* Desktop nav: hidden below lg, where it would otherwise clip. */}
        <nav className="hidden min-w-0 items-center gap-0.5 lg:flex xl:gap-1">
          {PRIMARY_LINKS.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.end} className={linkClass}>
              {link.label}
            </NavLink>
          ))}
          <InvestmentsDropdown />
          <NavLink to="/sips" className={linkClass}>
            SIPs
          </NavLink>
          <AnalyticsDropdown />
          <NavLink to="/news" className={linkClass}>
            News
          </NavLink>
          <NavLink to="/calculators" className={linkClass}>
            Calculators
          </NavLink>
        </nav>

        <div className="ml-auto flex shrink-0 items-center gap-2">
          {/* The full search input needs ~11rem the nav can't spare between lg
              and xl, so there it collapses to a palette trigger instead. */}
          <div className="hidden sm:max-lg:block xl:block">
            <NavbarSearch />
          </div>
          <button
            type="button"
            onClick={() => window.dispatchEvent(new CustomEvent('open-command-palette'))}
            aria-label="Search (Command K)"
            className="hidden items-center gap-2 rounded border border-border px-2.5 py-1.5 text-sm text-text-muted transition-colors hover:bg-surface-hover hover:text-text-primary lg:max-xl:flex"
          >
            <Search className="h-4 w-4" />
            <kbd className="text-[10px]">⌘K</kbd>
          </button>
          <AlertsBell />
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
            {PRIMARY_LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                onClick={close}
                className={mobileLinkClass}
              >
                {link.label}
              </NavLink>
            ))}

            <MobileGroupLabel>Investments</MobileGroupLabel>
            {INVESTMENT_LINKS.map((link) => (
              <NavLink key={link.to} to={link.to} onClick={close} className={mobileLinkClass}>
                {link.label}
              </NavLink>
            ))}

            <MobileGroupLabel>Analytics</MobileGroupLabel>
            {ANALYTICS_LINKS.map((link) =>
              link.to ? (
                <NavLink key={link.label} to={link.to} onClick={close} className={mobileLinkClass}>
                  {link.label}
                </NavLink>
              ) : (
                <span
                  key={link.label}
                  aria-disabled="true"
                  className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-text-muted opacity-60"
                >
                  {link.label}
                  <span className="rounded-full bg-surface-hover px-1.5 py-0.5 text-[10px]">
                    Soon
                  </span>
                </span>
              )
            )}

            <div className="mt-2 border-t border-border pt-2" />
            {SECONDARY_LINKS.map((link) => (
              <NavLink key={link.to} to={link.to} onClick={close} className={mobileLinkClass}>
                {link.label}
              </NavLink>
            ))}
          </nav>
        </div>
      )}
    </header>
  )
}
