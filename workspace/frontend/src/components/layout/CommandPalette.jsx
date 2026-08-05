/**
 * Command palette (§15.4) — ⌘K / Ctrl+K.
 *
 * Navigates to pages, calculators, and any asset already resolved into this app
 * (via §7's /api/search). It deliberately does NOT search the live universe:
 * that endpoint creates assets on select, and a palette is for getting
 * somewhere fast, not for silently adding rows to the catalogue.
 */

import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import {
  BarChart3,
  Calculator,
  CornerDownLeft,
  FileText,
  Home,
  Landmark,
  LineChart,
  Newspaper,
  PiggyBank,
  Receipt,
  Repeat,
  Search,
  Target,
  Wallet,
} from 'lucide-react'

import { useOwnSearch } from '../../hooks/useSearch'

const PAGES = [
  { id: 'home', label: 'Home', to: '/', icon: Home, hint: 'Dashboard' },
  { id: 'portfolio', label: 'My Portfolio', to: '/portfolio', icon: Wallet },
  { id: 'transactions', label: 'Transactions', to: '/transactions', icon: Receipt },
  { id: 'analytics', label: 'Advanced Analytics', to: '/analytics', icon: BarChart3 },
  // Goals is no longer a top-level nav item (it lives in Analytics → Projections),
  // so the palette is the main way to reach the full-page version.
  { id: 'goals', label: 'Goals', to: '/goals', icon: Target },
  { id: 'sips', label: 'SIPs', to: '/sips', icon: Repeat },
  { id: 'news', label: 'News', to: '/news', icon: Newspaper },
  { id: 'report', label: 'Portfolio report', to: '/report', icon: FileText, hint: 'Export PDF' },
  { id: 'stocks', label: 'Stocks', to: '/stocks', icon: LineChart },
  { id: 'funds', label: 'Mutual Funds', to: '/mutual-funds', icon: PiggyBank },
  { id: 'bonds', label: 'Bonds', to: '/bonds', icon: Landmark },
]

const CALCULATORS = [
  { id: 'calc', label: 'Calculators', to: '/calculators', icon: Calculator },
  {
    id: 'calc-hist',
    label: 'Historical returns calculator',
    to: '/calculators?tab=historical',
    icon: Calculator,
  },
  { id: 'calc-sip', label: 'SIP calculator', to: '/calculators?tab=sip', icon: Calculator },
  {
    id: 'calc-stepup',
    label: 'Step-up SIP calculator',
    to: '/calculators?tab=stepup',
    icon: Calculator,
  },
]

function score(text, query) {
  const haystack = text.toLowerCase()
  const needle = query.toLowerCase()
  if (!needle) return 0
  const index = haystack.indexOf(needle)
  if (index === 0) return 3
  if (index > 0) return 2
  // Subsequence match, so "mfnd" still finds "Mutual Funds".
  let cursor = 0
  for (const ch of needle) {
    cursor = haystack.indexOf(ch, cursor)
    if (cursor === -1) return -1
    cursor += 1
  }
  return 1
}

export default function CommandPalette() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const navigate = useNavigate()
  const listRef = useRef(null)

  const { data: assets = [] } = useOwnSearch(open ? query : '')

  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setOpen((v) => !v)
      } else if (e.key === 'Escape') {
        setOpen(false)
      }
    }
    // Also openable by click, so the palette isn't keyboard-discovery-only at
    // widths where the navbar drops its search input. An event keeps the two
    // components decoupled -- no shared context just to toggle a dialog.
    const onOpenRequest = () => setOpen(true)
    window.addEventListener('keydown', onKey)
    window.addEventListener('open-command-palette', onOpenRequest)
    return () => {
      window.removeEventListener('keydown', onKey)
      window.removeEventListener('open-command-palette', onOpenRequest)
    }
  }, [])

  useEffect(() => {
    if (!open) {
      setQuery('')
      setActive(0)
    }
  }, [open])

  const items = useMemo(() => {
    const staticItems = [...PAGES, ...CALCULATORS]
    const matched = query
      ? staticItems
          .map((item) => ({ item, s: score(item.label, query) }))
          .filter((x) => x.s > 0)
          .sort((a, b) => b.s - a.s)
          .map((x) => x.item)
      : staticItems

    const assetItems = assets.slice(0, 8).map((a) => ({
      id: `asset-${a.asset_id}`,
      label: a.name,
      hint: a.symbol?.replace(/\.(NS|BO)$/, ''),
      to: `/asset/${a.asset_id}`,
      icon: a.asset_type === 'MUTUAL_FUND' ? PiggyBank : a.asset_type === 'BOND' ? Landmark : LineChart,
      group: 'Your assets',
    }))

    return [
      ...matched.map((m) => ({ ...m, group: m.id.startsWith('calc') ? 'Calculators' : 'Go to' })),
      ...assetItems,
    ]
  }, [query, assets])

  useEffect(() => setActive(0), [query])

  const run = (item) => {
    if (!item) return
    setOpen(false)
    navigate(item.to)
  }

  const onKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActive((a) => Math.min(items.length - 1, a + 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActive((a) => Math.max(0, a - 1))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      run(items[active])
    }
  }

  useEffect(() => {
    listRef.current
      ?.querySelector(`[data-index="${active}"]`)
      ?.scrollIntoView({ block: 'nearest' })
  }, [active])

  let lastGroup = null

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-start justify-center p-4 pt-[12vh]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.14 }}
        >
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setOpen(false)}
            aria-hidden="true"
          />

          <motion.div
            role="dialog"
            aria-modal="true"
            aria-label="Command palette"
            initial={{ opacity: 0, scale: 0.97, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98, y: -4 }}
            transition={{ duration: 0.16 }}
            className="relative w-full max-w-xl overflow-hidden rounded border border-border bg-surface shadow-2xl"
          >
            <div className="flex items-center gap-2.5 border-b border-border px-4">
              <Search className="h-4 w-4 shrink-0 text-text-muted" />
              <input
                autoFocus
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Jump to a page, calculator, or asset…"
                className="h-12 w-full bg-transparent text-sm text-text-primary outline-none placeholder:text-text-muted"
              />
              <kbd className="shrink-0 rounded border border-border px-1.5 py-0.5 text-[10px] text-text-muted">
                ESC
              </kbd>
            </div>

            <div ref={listRef} className="max-h-[52vh] overflow-y-auto p-2">
              {items.length === 0 ? (
                <p className="px-3 py-6 text-center text-sm text-text-secondary">
                  Nothing matches “{query}”.
                </p>
              ) : (
                items.map((item, index) => {
                  const Icon = item.icon
                  const showGroup = item.group !== lastGroup
                  lastGroup = item.group
                  return (
                    <div key={item.id}>
                      {showGroup && (
                        <p className="px-3 pb-1 pt-2 text-[10px] font-medium uppercase tracking-wide text-text-muted">
                          {item.group}
                        </p>
                      )}
                      <button
                        type="button"
                        data-index={index}
                        onMouseEnter={() => setActive(index)}
                        onClick={() => run(item)}
                        className={`flex w-full items-center gap-3 rounded px-3 py-2 text-left text-sm transition-colors ${
                          index === active
                            ? 'bg-surface-hover text-text-primary'
                            : 'text-text-secondary hover:bg-surface-hover'
                        }`}
                      >
                        <Icon className="h-4 w-4 shrink-0 text-text-muted" />
                        <span className="min-w-0 flex-1 truncate">{item.label}</span>
                        {item.hint && (
                          <span className="shrink-0 text-xs text-text-muted">{item.hint}</span>
                        )}
                        {index === active && (
                          <CornerDownLeft className="h-3.5 w-3.5 shrink-0 text-text-muted" />
                        )}
                      </button>
                    </div>
                  )
                })
              )}
            </div>

            <div className="flex items-center gap-4 border-t border-border px-4 py-2 text-[11px] text-text-muted">
              <span className="flex items-center gap-1">
                <kbd className="rounded border border-border px-1">↑</kbd>
                <kbd className="rounded border border-border px-1">↓</kbd> navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="rounded border border-border px-1">↵</kbd> open
              </span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
