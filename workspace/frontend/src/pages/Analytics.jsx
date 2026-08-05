import { useState } from 'react'
import { Info } from 'lucide-react'

import { Badge, Button, Card, Input, Select, Skeleton } from '../components/ui'
import CorrelationMatrix from '../components/analytics/CorrelationMatrix'
import GoalsPanel from '../components/analytics/GoalsPanel'
import HealthScorePanel from '../components/analytics/HealthScorePanel'
import MarketMoodPanel from '../components/analytics/MarketMoodPanel'
import MonteCarloPanel from '../components/analytics/MonteCarloPanel'
import RebalancePanel from '../components/analytics/RebalancePanel'
import RiskMetricsPanel from '../components/analytics/RiskMetricsPanel'
import StatisticsPanel from '../components/analytics/StatisticsPanel'
import { useBenchmark } from '../hooks/useAdvancedAnalytics'
import { formatPercent } from '../utils/formatters'

const RISK_PERIODS = [
  { value: '1Y', label: '1 Year' },
  { value: '3Y', label: '3 Years' },
  { value: '5Y', label: '5 Years' },
  { value: 'ALL', label: 'All time' },
]

function BenchmarkPanel() {
  const [fdRate, setFdRate] = useState('7')
  const [inflationRate, setInflationRate] = useState('6')
  const { data, isLoading } = useBenchmark({
    codes: 'NIFTY50,SENSEX,GOLD',
    period: '1Y',
    fdRatePct: Number(fdRate) || undefined,
    inflationRatePct: Number(inflationRate) || undefined,
  })

  if (isLoading) return <Skeleton className="h-64 w-full rounded" />
  if (!data?.series?.length) {
    return <p className="text-sm text-text-secondary">Not enough data to compare yet.</p>
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-text-secondary">{data.note}</p>

      <div className="grid grid-cols-2 gap-4 sm:max-w-sm">
        <Input
          id="fd_rate"
          label="Assumed FD rate (%)"
          type="number"
          step="0.5"
          value={fdRate}
          onChange={(e) => setFdRate(e.target.value)}
        />
        <Input
          id="inflation_rate"
          label="Assumed inflation (%)"
          type="number"
          step="0.5"
          value={inflationRate}
          onChange={(e) => setInflationRate(e.target.value)}
        />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[34rem] text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase text-text-secondary">
              <th className="py-2 pr-4">Series</th>
              <th className="py-2 pr-4">Source</th>
              <th className="py-2 pr-4 text-right">Start</th>
              <th className="py-2 pr-4 text-right">End</th>
              <th className="py-2 text-right">Growth</th>
            </tr>
          </thead>
          <tbody>
            {data.series.map((s) => {
              const first = s.points[0]
              const last = s.points[s.points.length - 1]
              const growth = first && last ? (Number(last.value) / Number(first.value) - 1) * 100 : null
              return (
                <tr key={s.code} className="border-b border-border/50">
                  <td className="py-2 pr-4 text-text-primary">{s.label}</td>
                  <td className="py-2 pr-4">
                    {s.is_assumption ? (
                      <Badge tone="warning" title="User-editable assumption, not fetched market data">
                        Assumption
                      </Badge>
                    ) : (
                      <Badge tone="neutral">Market data</Badge>
                    )}
                  </td>
                  <td className="py-2 pr-4 text-right tabular-nums text-text-secondary">
                    {first ? Number(first.value).toFixed(1) : '—'}
                  </td>
                  <td className="py-2 pr-4 text-right tabular-nums text-text-secondary">
                    {last ? Number(last.value).toFixed(1) : '—'}
                  </td>
                  <td
                    className={`py-2 text-right tabular-nums ${
                      growth == null ? 'text-text-muted' : growth >= 0 ? 'text-positive' : 'text-negative'
                    }`}
                  >
                    {growth == null ? '—' : formatPercent(growth)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-text-muted">
        All series rebased to 100 at the start of the period. FD and inflation are assumptions you
        control above — they are not fetched market data.
      </p>
    </div>
  )
}

function Section({ title, subtitle, children }) {
  return (
    <Card className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-text-primary">{title}</h2>
        {subtitle && <p className="mt-0.5 text-sm text-text-secondary">{subtitle}</p>}
      </div>
      {children}
    </Card>
  )
}

export default function Analytics() {
  const [period, setPeriod] = useState('1Y')

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">Analytics</h1>
          <p className="mt-1 text-text-secondary">
            Risk, diversification and projections computed from your own holdings and cached price
            history.
          </p>
        </div>
        <div className="w-40">
          <Select
            id="analytics_period"
            label="Period"
            options={RISK_PERIODS}
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
          />
        </div>
      </div>

      <div className="flex items-start gap-2.5 rounded border border-border bg-surface px-4 py-3 text-sm text-text-secondary">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
        <p>
          Educational information only — not investment advice. These are simple, rule-based
          measures of your current allocation and past price behaviour. They don&apos;t predict
          future returns.
        </p>
      </div>

      <HealthScorePanel period={period} />

      <Section
        title="Risk metrics"
        subtitle="Computed from daily returns. Portfolio figures are time-weighted, so deposits and purchases don't count as performance."
      >
        <RiskMetricsPanel period={period} />
      </Section>

      <Section
        title="Correlation"
        subtitle="How closely your holdings move together. 1.0 means they move in lockstep; near 0 means they move independently."
      >
        <CorrelationMatrix period={period} />
      </Section>

      <Section title="Benchmark comparison" subtitle="Your portfolio against market indices and assumed rates.">
        <BenchmarkPanel />
      </Section>

      <Section title="Portfolio statistics" subtitle="Best and worst performers, win rate and holding periods.">
        <StatisticsPanel />
      </Section>

      <Section
        title="Monte Carlo projection"
        subtitle="Resamples your portfolio's own historical daily returns to show a range of possible outcomes."
      >
        <MonteCarloPanel />
      </Section>

      <Section
        title="Rebalancing simulator"
        subtitle="A what-if only — nothing is saved and no trade is placed."
      >
        <RebalancePanel period={period} />
      </Section>

      <Section title="Goals" subtitle="Progress measured against your total portfolio value.">
        <GoalsPanel />
      </Section>

      <Section title="Market mood" subtitle="Our own composite of breadth, momentum and volatility.">
        <MarketMoodPanel />
      </Section>
    </div>
  )
}
