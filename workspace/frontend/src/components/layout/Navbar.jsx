import { NavLink } from 'react-router-dom'
import { Search, Wallet } from 'lucide-react'
import { cn } from '../../utils/cn'
import Input from '../ui/Input'

const NAV_LINKS = [
  { to: '/', label: 'Home' },
  { to: '/portfolio', label: 'My Portfolio' },
  { to: '/transactions', label: 'Transactions' },
  { to: '/stocks', label: 'Stocks' },
  { to: '/mutual-funds', label: 'Mutual Funds' },
  { to: '/bonds', label: 'Bonds' },
]

export default function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-bg/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-6 px-6">
        <div className="flex items-center gap-2 text-text-primary">
          <Wallet className="h-5 w-5 text-accent" />
          <span className="text-sm font-semibold tracking-wide">Portfolio Manager</span>
        </div>

        <nav className="flex items-center gap-1">
          {NAV_LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === '/'}
              className={({ isActive }) =>
                cn(
                  'rounded px-3 py-1.5 text-sm font-medium transition-colors duration-150',
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

        <div className="ml-auto w-64">
          <Input
            type="search"
            icon={Search}
            placeholder="Search stocks, funds, bonds..."
            className="h-9"
          />
        </div>
      </div>
    </header>
  )
}
