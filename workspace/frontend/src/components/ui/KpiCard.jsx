import { useEffect, useState } from 'react'
import { animate, useMotionValue } from 'framer-motion'
import { ArrowUpRight, ArrowDownRight } from 'lucide-react'
import { cn } from '../../utils/cn'
import { formatCurrency, formatNumber, formatPercent } from '../../utils/formatters'
import Skeleton from './Skeleton'

function useCountUp(target, duration = 0.8) {
  const motionValue = useMotionValue(0)
  const [display, setDisplay] = useState(0)

  useEffect(() => {
    const controls = animate(motionValue, target, {
      duration,
      ease: 'easeOut',
      onUpdate: (v) => setDisplay(v),
    })
    return () => controls.stop()
  }, [target])

  return display
}

export default function KpiCard({
  label,
  value,
  changePct,
  format = 'currency',
  loading = false,
  className,
}) {
  const animatedValue = useCountUp(loading ? 0 : (value ?? 0))
  const isPositive = (changePct ?? 0) >= 0
  const Arrow = isPositive ? ArrowUpRight : ArrowDownRight

  const displayValue =
    format === 'currency'
      ? formatCurrency(animatedValue)
      : format === 'percent'
        ? formatPercent(animatedValue, { showSign: false })
        : formatNumber(animatedValue, { maximumFractionDigits: 0 })

  return (
    <div className={cn('rounded border border-border bg-surface p-5', className)}>
      <p className="text-xs font-medium uppercase tracking-wide text-text-secondary">{label}</p>
      {loading ? (
        <div className="mt-3 space-y-2">
          <Skeleton className="h-7 w-32" />
          <Skeleton className="h-4 w-20" />
        </div>
      ) : (
        <>
          <p className="mt-2 text-2xl font-semibold tabular-nums text-text-primary">
            {displayValue}
          </p>
          {changePct != null && (
            <p
              className={cn(
                'mt-1 flex items-center gap-1 text-sm font-medium tabular-nums',
                isPositive ? 'text-positive' : 'text-negative'
              )}
            >
              <Arrow className="h-4 w-4" />
              {formatPercent(changePct)}
            </p>
          )}
        </>
      )}
    </div>
  )
}
