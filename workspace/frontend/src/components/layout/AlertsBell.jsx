/**
 * In-app alerts bell + panel (§15.5).
 *
 * Every alert is recomputed server-side on each read, so there is no read/unread
 * state to keep and no risk of a stale "price target hit" lingering after the
 * price moved back. The panel states plainly that nothing is emailed or pushed:
 * there is no login or contact detail in this app to send anything to, and a
 * "notification sent" affordance would be fiction.
 */

import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { AlertTriangle, Bell, CalendarClock, Flag, Target } from 'lucide-react'

import { useAlerts } from '../../hooks/useVisualAnalytics'

const KIND_ICON = {
  PRICE_TARGET: Target,
  ALLOCATION_DRIFT: AlertTriangle,
  SIP_DUE: CalendarClock,
  MILESTONE: Flag,
}

const SEVERITY_TONE = {
  critical: 'text-negative',
  warning: 'text-warning',
  info: 'text-accent',
}

export default function AlertsBell() {
  const [open, setOpen] = useState(false)
  const { data, isLoading } = useAlerts()
  const containerRef = useRef(null)

  const alerts = data?.alerts ?? []
  const count = alerts.length

  useEffect(() => {
    if (!open) return undefined
    const onClick = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false)
    }
    const onKey = (e) => e.key === 'Escape' && setOpen(false)
    document.addEventListener('mousedown', onClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label={count ? `Alerts (${count})` : 'Alerts'}
        aria-expanded={open}
        className="relative rounded p-2 text-text-secondary transition-colors hover:bg-surface-hover hover:text-text-primary"
      >
        <Bell className="h-5 w-5" />
        {count > 0 && (
          <span className="absolute right-1 top-1 flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-accent px-1 text-[10px] font-semibold text-bg">
            {count > 9 ? '9+' : count}
          </span>
        )}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.99 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 z-50 mt-2 w-[min(22rem,calc(100vw-2rem))] overflow-hidden rounded border border-border bg-surface shadow-2xl"
          >
            <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
              <p className="text-sm font-medium text-text-primary">Alerts</p>
              <span className="text-xs text-text-muted">{count} active</span>
            </div>

            <div className="max-h-[60vh] overflow-y-auto">
              {isLoading ? (
                <p className="px-4 py-6 text-center text-sm text-text-secondary">Checking…</p>
              ) : count === 0 ? (
                <p className="px-4 py-6 text-center text-sm text-text-secondary">
                  Nothing needs your attention right now.
                </p>
              ) : (
                <ul className="divide-y divide-border/60">
                  {alerts.map((alert) => {
                    const Icon = KIND_ICON[alert.kind] ?? Bell
                    const body = (
                      <div className="flex gap-3 px-4 py-3">
                        <Icon
                          className={`mt-0.5 h-4 w-4 shrink-0 ${
                            SEVERITY_TONE[alert.severity] ?? 'text-text-muted'
                          }`}
                        />
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-text-primary">{alert.title}</p>
                          <p className="mt-0.5 text-xs leading-relaxed text-text-secondary">
                            {alert.body}
                          </p>
                        </div>
                      </div>
                    )
                    return (
                      <li key={alert.id}>
                        {alert.asset_id ? (
                          <Link
                            to={`/asset/${alert.asset_id}`}
                            onClick={() => setOpen(false)}
                            className="block transition-colors hover:bg-surface-hover"
                          >
                            {body}
                          </Link>
                        ) : (
                          body
                        )}
                      </li>
                    )
                  })}
                </ul>
              )}
            </div>

            <p className="border-t border-border px-4 py-2.5 text-[11px] leading-relaxed text-text-muted">
              Recomputed each time you open this panel. In-app only — this app has no login or
              contact details, so nothing is emailed or pushed.
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
