/**
 * Home hero (§15.1 ambient layer + §15.3 glass/glow treatment).
 *
 * The Three.js field sits behind the numbers at low opacity and is purely
 * decorative -- every figure it tints is also printed here as text.
 */

import { lazy, Suspense, useEffect, useState } from 'react'
import { animate, useMotionValue } from 'framer-motion'
import { ArrowDownRight, ArrowUpRight } from 'lucide-react'

import { Skeleton } from '../ui'
import { cn } from '../../utils/cn'
import { formatCurrency, formatPercent } from '../../utils/formatters'

// Three.js is ~600kB and this layer is pure decoration, so it must never be on
// the critical path to the user's portfolio value. Lazy-loaded with a null
// fallback: the hero renders complete without it and the field fades in after.
const AmbientField = lazy(() => import('../three/AmbientField'))

function useCountUp(target, duration = 0.9) {
  const motionValue = useMotionValue(0)
  const [display, setDisplay] = useState(0)
  useEffect(() => {
    const controls = animate(motionValue, target, {
      duration,
      ease: 'easeOut',
      onUpdate: setDisplay,
    })
    return () => controls.stop()
  }, [target]) // eslint-disable-line react-hooks/exhaustive-deps
  return display
}

function Stat({ label, value, pct }) {
  const positive = (pct ?? 0) >= 0
  const Arrow = positive ? ArrowUpRight : ArrowDownRight
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-text-secondary">{label}</p>
      <p
        className={cn(
          'mt-1 text-lg font-semibold tabular-nums sm:text-xl',
          positive ? 'text-positive' : 'text-negative'
        )}
      >
        {formatCurrency(value)}
      </p>
      {pct != null && (
        <p
          className={cn(
            'mt-0.5 flex items-center gap-1 text-sm tabular-nums',
            positive ? 'text-positive' : 'text-negative'
          )}
        >
          <Arrow className="h-3.5 w-3.5" />
          {formatPercent(pct)}
        </p>
      )}
    </div>
  )
}

export default function PortfolioHero({ totalValue, dayPl, dayPlPct, totalPl, totalPlPct, loading }) {
  const animatedTotal = useCountUp(loading ? 0 : (totalValue ?? 0))

  // Drives only the ambient tint. Scaled so a ~2% day is a full-strength
  // colour -- a normalization for decoration, not a published statistic.
  const intensity = Math.max(-1, Math.min(1, (dayPlPct ?? 0) / 2))

  return (
    <section className="relative isolate overflow-hidden rounded border border-border bg-surface">
      <Suspense fallback={null}>
        <AmbientField intensity={intensity} />
      </Suspense>

      {/* Glass wash + a soft accent glow, per §15.3 -- hero only, never over a
          data table. */}
      <div
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          background:
            'radial-gradient(80% 120% at 12% 0%, color-mix(in srgb, var(--accent) 12%, transparent) 0%, transparent 60%)',
        }}
      />

      <div className="relative p-5 backdrop-blur-[2px] sm:p-6">
        <p className="text-xs font-medium uppercase tracking-wide text-text-secondary">
          Total portfolio value
        </p>

        {loading ? (
          <Skeleton className="mt-2 h-10 w-56" />
        ) : (
          <p className="mt-1 text-3xl font-semibold tabular-nums text-text-primary sm:text-4xl">
            {formatCurrency(animatedTotal)}
          </p>
        )}

        <div className="mt-5 grid grid-cols-2 gap-4 border-t border-border/70 pt-4 sm:max-w-md">
          {loading ? (
            <>
              <Skeleton className="h-14 w-full" />
              <Skeleton className="h-14 w-full" />
            </>
          ) : (
            <>
              <Stat label="Today" value={dayPl} pct={dayPlPct} />
              <Stat label="Total P/L" value={totalPl} pct={totalPlPct} />
            </>
          )}
        </div>
      </div>
    </section>
  )
}
