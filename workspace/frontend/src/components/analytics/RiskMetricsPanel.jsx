import { Skeleton } from '../ui'
import { useRisk } from '../../hooks/useAdvancedAnalytics'

// Formatters differ per metric: some are percentages of value, some are bare
// ratios. Rendering a Sharpe ratio as "-0.58%" would be wrong, so each metric
// declares how to display itself.
const METRICS = [
  {
    key: 'volatility',
    label: 'Volatility (annualized)',
    kind: 'pct',
    help: 'How much the value swings year to year. Higher means bigger moves in both directions.',
  },
  {
    key: 'annualized_return',
    label: 'Return (annualized)',
    kind: 'pct',
    signed: true,
    help: 'Average daily return scaled to a year.',
  },
  {
    key: 'sharpe',
    label: 'Sharpe ratio',
    kind: 'ratio',
    signed: true,
    help: 'Return above the risk-free rate per unit of total volatility. Higher is better.',
  },
  {
    key: 'sortino',
    label: 'Sortino ratio',
    kind: 'ratio',
    signed: true,
    help: 'Like Sharpe, but only counts downside volatility as risk.',
  },
  {
    key: 'max_drawdown',
    label: 'Max drawdown',
    kind: 'pct',
    negative: true,
    help: 'Largest peak-to-trough fall over the period.',
  },
  {
    key: 'var_95',
    label: 'Value at Risk (95%)',
    kind: 'pct',
    negative: true,
    help: 'On the worst 5% of days historically, the loss was at least this much.',
  },
  {
    key: 'calmar',
    label: 'Calmar ratio',
    kind: 'ratio',
    signed: true,
    help: 'Annualized return divided by the worst drawdown.',
  },
  {
    key: 'beta',
    label: 'Beta vs NIFTY 50',
    kind: 'ratio',
    help: '1.0 moves with the index; above 1 amplifies it, below 1 dampens it.',
  },
  {
    key: 'tracking_error',
    label: 'Tracking error',
    kind: 'pct',
    help: 'How far the portfolio drifts from the index.',
  },
]

function formatMetric(value, metric) {
  if (value == null) return { text: 'not measurable', tone: 'text-text-muted' }

  if (metric.kind === 'pct') {
    const pct = value * 100
    const text = `${pct.toFixed(2)}%`
    if (metric.negative) return { text, tone: 'text-negative' }
    if (metric.signed) {
      return { text: `${pct >= 0 ? '+' : ''}${text}`, tone: pct >= 0 ? 'text-positive' : 'text-negative' }
    }
    return { text, tone: 'text-text-primary' }
  }

  const text = value.toFixed(2)
  if (metric.signed) {
    return { text: `${value >= 0 ? '+' : ''}${text}`, tone: value >= 0 ? 'text-positive' : 'text-negative' }
  }
  return { text, tone: 'text-text-primary' }
}

export default function RiskMetricsPanel({ period = '1Y' }) {
  const { data, isLoading } = useRisk({ scope: 'portfolio', period })

  if (isLoading) return <Skeleton className="h-64 w-full rounded" />
  if (!data) return null

  if (!data.sufficient_data) {
    return (
      <p className="text-sm text-text-secondary">
        Not enough price history to measure risk over this period ({data.observations} daily
        observations).
      </p>
    )
  }

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2 lg:grid-cols-3">
        {METRICS.map((metric) => {
          const { text, tone } = formatMetric(data[metric.key], metric)
          return (
            <div key={metric.key} className="rounded border border-border bg-bg p-3">
              <div className="flex items-baseline justify-between gap-2">
                <span className="text-xs text-text-secondary">{metric.label}</span>
                <span className={`tabular-nums text-sm font-medium ${tone}`}>{text}</span>
              </div>
              <p className="mt-1 text-xs leading-snug text-text-muted">{metric.help}</p>
            </div>
          )
        })}
      </div>
      <p className="text-xs text-text-muted">
        Based on {data.observations} daily observations over {data.period}, against{' '}
        {data.benchmark_code}. Risk-free rate assumed at {data.risk_free_rate_pct}% — an assumption,
        not fetched data.
      </p>
    </div>
  )
}
