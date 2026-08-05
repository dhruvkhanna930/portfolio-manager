import { Skeleton } from '../ui'
import { useMarketMood } from '../../hooks/useAdvancedAnalytics'

const BAND_TONE = {
  'Very Bullish': 'text-positive',
  Bullish: 'text-positive',
  Neutral: 'text-text-primary',
  Bearish: 'text-negative',
  'Very Bearish': 'text-negative',
}

const COMPONENT_LABELS = {
  breadth: 'Breadth',
  momentum: 'Momentum',
  calm: 'Calm (inverse volatility)',
}

function detailText(name, detail) {
  if (!detail || Object.keys(detail).length === 0) return null
  if (name === 'breadth') {
    return `${detail.advancers} up / ${detail.decliners} down of ${detail.measured} measured`
  }
  if (name === 'momentum') {
    return `5-day avg ${detail.ma5} vs 20-day avg ${detail.ma20} (${
      detail.spread_pct >= 0 ? '+' : ''
    }${detail.spread_pct}%)`
  }
  if (name === 'calm') {
    return `${detail.annualized_volatility_pct}% annualized volatility`
  }
  return null
}

export default function MarketMoodPanel() {
  const { data, isLoading } = useMarketMood()

  if (isLoading) return <Skeleton className="h-48 w-full rounded" />
  if (!data) return null

  if (data.insufficient_data) {
    return <p className="text-sm text-text-secondary">{data.reason ?? 'Not enough data yet.'}</p>
  }

  return (
    <div className="space-y-4">
      <div className="flex items-baseline gap-3">
        <span className="text-4xl font-semibold tabular-nums text-text-primary">{data.score}</span>
        <span className="text-lg text-text-muted">/ 100</span>
        <span className={`text-sm ${BAND_TONE[data.band] ?? 'text-text-secondary'}`}>{data.band}</span>
      </div>

      <div className="space-y-3">
        {Object.entries(data.components).map(([name, component]) => (
          <div key={name}>
            <div className="flex items-baseline justify-between gap-3">
              <span className="text-sm text-text-primary">{COMPONENT_LABELS[name] ?? name}</span>
              <span className="tabular-nums text-sm text-text-primary">
                {component.score == null ? (
                  <span className="text-text-muted">not measurable</span>
                ) : (
                  component.score.toFixed(1)
                )}
                <span className="ml-2 text-xs text-text-muted">×{component.weight}</span>
              </span>
            </div>
            {component.score != null && (
              <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-surface-hover">
                <div
                  className="h-full rounded-full bg-accent"
                  style={{ width: `${Math.max(0, Math.min(100, component.score))}%` }}
                />
              </div>
            )}
            <p className="mt-1 text-xs text-text-muted">
              {detailText(name, component.detail) ?? component.explanation}
            </p>
          </div>
        ))}
      </div>

      <p className="text-xs text-text-muted">{data.methodology}</p>
      <p className="border-t border-border pt-3 text-xs text-text-muted">{data.disclaimer}</p>
    </div>
  )
}
