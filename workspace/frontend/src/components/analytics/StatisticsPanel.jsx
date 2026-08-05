import { Link } from 'react-router-dom'

import { Skeleton } from '../ui'
import { useStatistics } from '../../hooks/useAdvancedAnalytics'
import { formatCurrency, formatDate, formatPercent } from '../../utils/formatters'

function Stat({ label, children, help }) {
  return (
    <div className="rounded border border-border bg-bg p-3">
      <p className="text-xs text-text-secondary">{label}</p>
      <div className="mt-1 text-sm text-text-primary">{children}</div>
      {help && <p className="mt-1 text-xs text-text-muted">{help}</p>}
    </div>
  )
}

function PerformerLine({ performer }) {
  if (!performer) return <span className="text-text-muted">—</span>
  const pct = Number(performer.profit_loss_pct)
  return (
    <Link to={`/asset/${performer.asset_id}`} className="hover:text-accent hover:underline">
      <span className="font-medium">{performer.symbol.replace(/\.(NS|BO)$/, '')}</span>{' '}
      <span className={pct >= 0 ? 'text-positive' : 'text-negative'}>{formatPercent(pct)}</span>
    </Link>
  )
}

export default function StatisticsPanel() {
  const { data, isLoading } = useStatistics()

  if (isLoading) return <Skeleton className="h-48 w-full rounded" />
  if (!data?.has_holdings) {
    return <p className="text-sm text-text-secondary">No holdings yet.</p>
  }

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Stat label="Best performer" help="Unrealised, by percentage">
          <PerformerLine performer={data.best_performer} />
        </Stat>
        <Stat label="Worst performer" help="Unrealised, by percentage">
          <PerformerLine performer={data.worst_performer} />
        </Stat>
        <Stat label="Win rate" help={data.notes?.win_rate}>
          {data.win_rate_pct == null ? '—' : `${Number(data.win_rate_pct).toFixed(1)}%`}{' '}
          <span className="text-text-muted">
            ({data.winners_count}W / {data.losers_count}L)
          </span>
        </Stat>
        <Stat label="Average holding period">
          {data.avg_holding_period_days == null ? '—' : `${data.avg_holding_period_days} days`}
        </Stat>
        <Stat label="Longest held">
          {data.longest_held ? (
            <Link to={`/asset/${data.longest_held.asset_id}`} className="hover:text-accent hover:underline">
              <span className="font-medium">{data.longest_held.symbol.replace(/\.(NS|BO)$/, '')}</span>{' '}
              <span className="text-text-secondary">
                {data.longest_held.days_held}d · since {formatDate(data.longest_held.first_bought)}
              </span>
            </Link>
          ) : (
            '—'
          )}
        </Stat>
        <Stat label="Turnover" help={data.notes?.turnover}>
          {data.turnover_ratio == null ? '—' : `${(Number(data.turnover_ratio) * 100).toFixed(1)}%`}
        </Stat>
        <Stat label="Largest realised gain" help={data.notes?.largest_gain_loss}>
          {data.largest_gain ? (
            <span className="text-positive">
              {formatCurrency(data.largest_gain.realised_pl)}{' '}
              <span className="text-text-muted">
                ({data.largest_gain.symbol.replace(/\.(NS|BO)$/, '')})
              </span>
            </span>
          ) : (
            <span className="text-text-muted">No realised gains yet</span>
          )}
        </Stat>
        <Stat label="Largest realised loss" help={data.notes?.largest_gain_loss}>
          {data.largest_loss ? (
            <span className="text-negative">
              {formatCurrency(data.largest_loss.realised_pl)}{' '}
              <span className="text-text-muted">
                ({data.largest_loss.symbol.replace(/\.(NS|BO)$/, '')})
              </span>
            </span>
          ) : (
            <span className="text-text-muted">No realised losses yet</span>
          )}
        </Stat>
        <Stat label="Realised trades">{data.realised_trades_count}</Stat>
      </div>

      {data.priced_holdings_count < data.holdings_count && (
        <p className="text-xs text-text-muted">
          {data.holdings_count - data.priced_holdings_count} holding(s) have no current price, so
          they&apos;re excluded from best/worst and win rate.
        </p>
      )}
    </div>
  )
}
