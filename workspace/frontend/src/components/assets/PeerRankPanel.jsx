/**
 * Peer ranking (§15.4).
 *
 * The scope caveat is not fine print here — it's rendered next to the rank
 * itself. "#2 of 5" is only meaningful once you know the 5 are the assets this
 * user happens to have added, not a sector universe, so the panel says exactly
 * that where the number is, not in a footnote.
 */

import { Link } from 'react-router-dom'

import { Badge, Skeleton } from '../ui'
import { usePeerRank } from '../../hooks/useVisualAnalytics'
import { formatPercent } from '../../utils/formatters'

function cleanSymbol(symbol) {
  return String(symbol ?? '').replace(/\.(NS|BO)$/, '')
}

export default function PeerRankPanel({ assetId, period = '1Y' }) {
  const { data, isLoading } = usePeerRank(assetId, period)

  if (isLoading) return <Skeleton className="h-40 w-full rounded" />
  if (!data) return null

  if (data.rank == null || data.total < 2) {
    return (
      <p className="text-sm text-text-secondary">
        {data.reason ??
          'Not enough comparable assets in your own list to rank this one yet. Add more from the same sector to enable the comparison.'}
      </p>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="text-2xl font-semibold tabular-nums text-text-primary">
          #{data.rank}
        </span>
        <span className="text-sm text-text-secondary">
          of {data.total} · {data.comparison_basis}
        </span>
        <Badge tone="neutral" title={data.scope_note}>
          Your list only
        </Badge>
      </div>

      <ul className="divide-y divide-border/60">
        {data.peers.map((peer) => (
          <li
            key={peer.asset_id}
            className={`flex items-center gap-3 py-2 text-sm ${
              peer.is_current ? 'rounded bg-surface-hover px-2' : ''
            }`}
          >
            <span className="w-6 shrink-0 tabular-nums text-text-muted">{peer.rank}</span>
            <span className="min-w-0 flex-1 truncate">
              {peer.is_current ? (
                <span className="font-medium text-text-primary">
                  {cleanSymbol(peer.symbol)} <span className="text-text-muted">(this asset)</span>
                </span>
              ) : (
                <Link
                  to={`/asset/${peer.asset_id}`}
                  className="text-text-secondary hover:text-text-primary"
                >
                  {cleanSymbol(peer.symbol)}
                </Link>
              )}
            </span>
            <span
              className={`shrink-0 tabular-nums ${
                peer.return_pct >= 0 ? 'text-positive' : 'text-negative'
              }`}
            >
              {formatPercent(peer.return_pct)}
            </span>
          </li>
        ))}
      </ul>

      <p className="text-xs text-text-muted">
        {data.scope_note} Ranked on total return over {data.period} from cached price history.
      </p>
    </div>
  )
}
