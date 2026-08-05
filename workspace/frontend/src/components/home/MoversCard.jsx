import { Link } from 'react-router-dom'
import { TrendingDown, TrendingUp } from 'lucide-react'
import { Card, EmptyState, Skeleton } from '../ui'
import { formatCurrency, formatPercent } from '../../utils/formatters'

function MoverRow({ item }) {
  const pct = Number(item.day_change_pct)
  const isUp = pct >= 0
  return (
    <Link
      to={`/asset/${item.asset_id}`}
      className="flex items-center justify-between gap-3 rounded px-2 py-2 transition-colors hover:bg-surface-hover"
    >
      <div className="min-w-0">
        <p className="truncate text-sm font-medium text-text-primary">{item.name}</p>
        <p className="text-xs text-text-muted">{item.symbol}</p>
      </div>
      <div className="shrink-0 text-right">
        <p className="tabular-nums text-sm text-text-primary">{formatCurrency(item.price)}</p>
        <p className={`tabular-nums text-xs font-medium ${isUp ? 'text-positive' : 'text-negative'}`}>
          {formatPercent(pct)}
        </p>
      </div>
    </Link>
  )
}

function MoversList({ items, loading, emptyMessage }) {
  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-11 w-full rounded" />
        ))}
      </div>
    )
  }
  if (!items || items.length === 0) {
    return <EmptyState title={emptyMessage} className="py-6" />
  }
  return (
    <div className="space-y-0.5">
      {items.map((item) => (
        <MoverRow key={item.asset_id} item={item} />
      ))}
    </div>
  )
}

export default function MoversCard({ title, subtitle, gainers, losers, loading }) {
  return (
    <Card>
      <div className="mb-3">
        <h2 className="text-sm font-medium uppercase tracking-wide text-text-secondary">{title}</h2>
        {subtitle && <p className="mt-0.5 text-xs text-text-muted">{subtitle}</p>}
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <p className="mb-1 flex items-center gap-1.5 text-xs font-medium text-positive">
            <TrendingUp className="h-3.5 w-3.5" />
            Top Gainers
          </p>
          <MoversList items={gainers} loading={loading} emptyMessage="No gainers" />
        </div>
        <div>
          <p className="mb-1 flex items-center gap-1.5 text-xs font-medium text-negative">
            <TrendingDown className="h-3.5 w-3.5" />
            Top Losers
          </p>
          <MoversList items={losers} loading={loading} emptyMessage="No losers" />
        </div>
      </div>
    </Card>
  )
}
