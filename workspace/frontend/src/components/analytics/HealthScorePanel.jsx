import { AlertTriangle, CheckCircle2, Lightbulb } from 'lucide-react'

import { Card, Skeleton } from '../ui'
import { useHealthScore } from '../../hooks/useAdvancedAnalytics'

const BAND_TONE = {
  Strong: 'text-positive',
  Moderate: 'text-warning',
  'Needs attention': 'text-negative',
}

const COMPONENT_LABELS = {
  diversification: 'Diversification',
  cash_reserve: 'Cash reserve',
  volatility: 'Volatility (lower is better)',
  sector_balance: 'Sector balance',
}

function ComponentRow({ name, component }) {
  const score = component.score
  return (
    <div className="border-b border-border/50 py-3 last:border-0">
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-sm text-text-primary">{COMPONENT_LABELS[name] ?? name}</span>
        <span className="tabular-nums text-sm text-text-primary">
          {score == null ? <span className="text-text-muted">not measurable</span> : `${score.toFixed(1)} / 100`}
          <span className="ml-2 text-xs text-text-muted">×{component.weight}</span>
        </span>
      </div>
      {score != null && (
        <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-surface-hover">
          <div className="h-full rounded-full bg-accent" style={{ width: `${Math.max(0, Math.min(100, score))}%` }} />
        </div>
      )}
      <p className="mt-1.5 text-xs text-text-muted">{component.explanation}</p>
    </div>
  )
}

function InsightList({ icon: Icon, title, items, tone }) {
  if (!items?.length) return null
  return (
    <div>
      <p className={`mb-1.5 flex items-center gap-1.5 text-sm font-medium ${tone}`}>
        <Icon className="h-4 w-4" />
        {title}
      </p>
      <ul className="space-y-1">
        {items.map((text) => (
          <li key={text} className="text-sm text-text-secondary">
            • {text}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function HealthScorePanel({ period = '1Y' }) {
  const { data, isLoading } = useHealthScore(period)

  if (isLoading) return <Skeleton className="h-72 w-full rounded" />
  if (!data) return null

  if (data.insufficient_data) {
    return (
      <Card>
        <h2 className="text-lg font-semibold text-text-primary">Portfolio Health Score</h2>
        <p className="mt-2 text-sm text-text-secondary">{data.reason}</p>
      </Card>
    )
  }

  return (
    <Card className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-text-primary">Portfolio Health Score</h2>
          <p className="mt-0.5 text-sm text-text-secondary">
            A weighted composite of the four measures below.
          </p>
        </div>
        <div className="text-right">
          <div className="text-4xl font-semibold tabular-nums text-text-primary">
            {data.health_score}
            <span className="text-lg text-text-muted"> / 100</span>
          </div>
          <div className={`text-sm ${BAND_TONE[data.band] ?? 'text-text-secondary'}`}>{data.band}</div>
        </div>
      </div>

      <div>
        {Object.entries(data.components).map(([name, component]) => (
          <ComponentRow key={name} name={name} component={component} />
        ))}
      </div>

      {data.excluded_components?.length > 0 && (
        <p className="text-xs text-text-muted">
          Excluded from the score (not enough data): {data.excluded_components.join(', ')}. The
          remaining weights were rescaled so the total still adds up to 100.
        </p>
      )}

      <div className="space-y-3">
        <InsightList icon={CheckCircle2} title="Strengths" items={data.insights.strengths} tone="text-positive" />
        <InsightList icon={AlertTriangle} title="Worth watching" items={data.insights.watchouts} tone="text-warning" />
        <InsightList icon={Lightbulb} title="Things to consider" items={data.insights.suggestions} tone="text-accent" />
      </div>

      <p className="border-t border-border pt-3 text-xs text-text-muted">{data.disclaimer}</p>
    </Card>
  )
}
