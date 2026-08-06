/**
 * One ranked candidate.
 *
 * Deliberately not styled as a call to action. §13 requires these read as
 * educational, so the card leads with *why* it ranked where it did and links to
 * the asset's own detail page rather than offering a Buy button.
 */

import { Link } from 'react-router-dom'
import { ArrowUpRight, Minus, TrendingDown, TrendingUp } from 'lucide-react'

import { Badge } from '../ui'
import ScoreBreakdown from './ScoreBreakdown'
import { formatNumber } from '../../utils/formatters'

const CONFIDENCE_TONE = {
  high: 'positive',
  medium: 'neutral',
  low: 'warning',
}

function Metric({ label, value, suffix = '' }) {
  return (
    <div className="min-w-0">
      <dt className="text-[11px] uppercase tracking-wide text-text-muted">{label}</dt>
      <dd className="truncate text-sm tabular-nums text-text-primary">
        {value == null ? '—' : `${formatNumber(value, { maximumFractionDigits: 2 })}${suffix}`}
      </dd>
    </div>
  )
}

export default function RecommendationCard({ item, rank }) {
  const { fundamentals = {}, reasons = [] } = item

  return (
    <div className="rounded border border-border bg-surface p-4 transition-colors hover:border-border/80">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <span className="mt-0.5 shrink-0 rounded bg-surface-hover px-2 py-1 text-xs font-medium tabular-nums text-text-secondary">
            #{rank}
          </span>
          <div className="min-w-0">
            <Link
              to={`/asset/${item.asset_id}`}
              className="flex items-center gap-1 text-sm font-medium text-text-primary hover:text-accent"
            >
              <span className="truncate">{item.name}</span>
              <ArrowUpRight className="h-3.5 w-3.5 shrink-0" />
            </Link>
            <p className="mt-0.5 truncate text-xs text-text-secondary">
              {item.symbol?.replace(/\.(NS|BO)$/, '')}
              {item.sector ? ` · ${item.sector}` : ''}
            </p>
          </div>
        </div>

        <div className="shrink-0 text-right">
          <p className="text-lg font-semibold tabular-nums text-text-primary">
            {item.final_score?.toFixed(1)}
          </p>
          <Badge tone={CONFIDENCE_TONE[item.confidence] || 'neutral'}>
            {item.confidence} confidence
          </Badge>
        </div>
      </div>

      <div className="mt-4">
        <ScoreBreakdown
          components={item.components}
          weights={item.weights_applied}
          finalScore={item.final_score}
        />
      </div>

      {reasons.length > 0 && (
        <ul className="mt-3 space-y-1">
          {reasons.map((reason) => {
            const Icon =
              reason.direction === 'supports'
                ? TrendingUp
                : reason.direction === 'weighs against'
                  ? TrendingDown
                  : Minus
            const tone =
              reason.direction === 'supports' ? 'text-positive' : 'text-negative'
            return (
              <li
                key={reason.factor}
                className="flex items-start gap-2 text-xs text-text-secondary"
              >
                <Icon className={`mt-0.5 h-3.5 w-3.5 shrink-0 ${tone}`} />
                <span>
                  {reason.direction === 'supports' ? 'Supports' : 'Weighs against'}:{' '}
                  {reason.factor}
                </span>
              </li>
            )
          })}
        </ul>
      )}

      <dl className="mt-4 grid grid-cols-2 gap-3 border-t border-border pt-3 sm:grid-cols-4">
        <Metric label="P/E" value={fundamentals.pe_ratio} />
        <Metric label="Beta" value={fundamentals.beta} />
        <Metric label="Div yield" value={fundamentals.dividend_yield} suffix="%" />
        <Metric label="Profit margin" value={fundamentals.profit_margin} suffix="%" />
      </dl>
    </div>
  )
}
