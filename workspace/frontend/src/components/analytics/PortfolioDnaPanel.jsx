/**
 * Portfolio DNA (§15.2 radar) — sector and asset-class exposure side by side.
 *
 * The radar shows shape; the list beside it shows the exact percentages, so the
 * chart never has to be read precisely to get the number.
 */

import { useState } from 'react'

import { Skeleton, Tabs } from '../ui'
import PortfolioRadar from '../charts/PortfolioRadar'
import { useAllocation } from '../../hooks/useAnalytics'
import { formatCurrency } from '../../utils/formatters'
import { seriesColor } from '../charts/chartTheme'

const DIMENSIONS = [
  { key: 'sector', label: 'By sector' },
  { key: 'type', label: 'By asset class' },
]

export default function PortfolioDnaPanel() {
  const [dimension, setDimension] = useState('sector')
  const { data, isLoading } = useAllocation(dimension)

  const items = data?.items ?? []

  return (
    <div className="space-y-4">
      <Tabs tabs={DIMENSIONS} value={dimension} onChange={setDimension} className="w-fit" />

      {isLoading ? (
        <Skeleton className="h-72 w-full rounded" />
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_minmax(0,18rem)]">
          <PortfolioRadar items={items} height={300} />

          <ul className="space-y-2 self-center">
            {[...items]
              .sort((a, b) => Number(b.pct) - Number(a.pct))
              .map((item, i) => (
                <li key={item.label} className="flex items-center gap-2.5 text-sm">
                  <span
                    className="h-2.5 w-2.5 shrink-0 rounded-sm"
                    style={{ background: seriesColor(i) }}
                  />
                  <span className="min-w-0 flex-1 truncate text-text-primary">{item.label}</span>
                  <span className="shrink-0 tabular-nums text-text-secondary">
                    {Number(item.pct).toFixed(1)}%
                  </span>
                  <span className="w-24 shrink-0 text-right tabular-nums text-text-muted">
                    {formatCurrency(item.value)}
                  </span>
                </li>
              ))}
          </ul>
        </div>
      )}
    </div>
  )
}
