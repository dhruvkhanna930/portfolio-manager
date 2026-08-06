import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Info } from 'lucide-react'

import { Badge, Card, Input, Select, Skeleton, Tabs } from '../components/ui'
import BenchmarkOverlayChart from '../components/charts/BenchmarkOverlayChart'
import CashflowPanel from '../components/analytics/CashflowPanel'
import CorrelationMatrix from '../components/analytics/CorrelationMatrix'
import GoalsPanel from '../components/analytics/GoalsPanel'
import HealthScorePanel from '../components/analytics/HealthScorePanel'
import MarketMoodPanel from '../components/analytics/MarketMoodPanel'
import MonteCarloPanel from '../components/analytics/MonteCarloPanel'
import PortfolioDnaPanel from '../components/analytics/PortfolioDnaPanel'
import RebalancePanel from '../components/analytics/RebalancePanel'
import ReportExportButton from '../components/report/ReportExportButton'
import RiskMetricsPanel from '../components/analytics/RiskMetricsPanel'
import RiskReturnPanel from '../components/analytics/RiskReturnPanel'
import StatisticsPanel from '../components/analytics/StatisticsPanel'
import TimelinePanel from '../components/analytics/TimelinePanel'
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

      <BenchmarkOverlayChart series={data.series} />

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

function Section({ title, subtitle, action, children }) {
  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold text-text-primary">{title}</h2>
          {subtitle && <p className="mt-0.5 text-sm text-text-secondary">{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </Card>
  )
}

const VIEWS = [
  { key: 'overview', label: 'Overview' },
  { key: 'risk', label: 'Risk' },
  { key: 'performance', label: 'Performance' },
  { key: 'projections', label: 'Projections' },
  { key: 'activity', label: 'Activity' },
]

export default function Analytics() {
  const [period, setPeriod] = useState('1Y')
  const [view, setView] = useState('overview')

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
        <div className="flex items-end gap-2">
          <ReportExportButton period={period} />
          <div className="w-36">
            <Select
              id="analytics_period"
              label="Period"
              options={RISK_PERIODS}
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
            />
          </div>
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

      <Tabs tabs={VIEWS} value={view} onChange={setView} />

      <AnimatePresence mode="wait">
        <motion.div
          key={view}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2 }}
          className="space-y-6"
        >
          {view === 'overview' && (
            <>
              <HealthScorePanel period={period} />

              <Section
                title="Portfolio DNA"
                subtitle="The shape of your exposure across sectors and asset classes."
              >
                <PortfolioDnaPanel />
              </Section>

              <Section
                title="Market mood"
                subtitle="Our own composite of breadth, momentum and volatility."
              >
                <MarketMoodPanel />
              </Section>
            </>
          )}

          {view === 'risk' && (
            <>
              <Section
                title="Risk metrics"
                subtitle="Computed from daily returns. Portfolio figures are time-weighted, so deposits and purchases don't count as performance."
              >
                <RiskMetricsPanel period={period} />
              </Section>

              <Section
                title="Risk vs. return"
                subtitle="Each holding placed by its own volatility and return. Bubble size is position value."
              >
                <RiskReturnPanel period={period} />
              </Section>

              <Section
                title="Correlation"
                subtitle="How closely your holdings move together. Green pairs diversify each other; red pairs move as one."
              >
                <CorrelationMatrix period={period} />
              </Section>
            </>
          )}

          {view === 'performance' && (
            <>
              <Section
                title="Benchmark comparison"
                subtitle="Your portfolio against market indices and assumed rates, all rebased to 100."
              >
                <BenchmarkPanel />
              </Section>

              <Section
                title="Portfolio statistics"
                subtitle="Best and worst performers, win rate and holding periods."
              >
                <StatisticsPanel />
              </Section>
            </>
          )}

          {view === 'projections' && (
            <>
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

              <Section
                title="Goals"
                subtitle="Progress measured against your total portfolio value."
                action={
                  <Link
                    to="/goals"
                    className="whitespace-nowrap text-sm text-accent hover:text-accent-hover"
                  >
                    Open Goals page →
                  </Link>
                }
              >
                <GoalsPanel />
              </Section>
            </>
          )}

          {view === 'activity' && (
            <>
              <Section
                title="Timeline"
                subtitle="Your transaction history, and what the portfolio looked like on any past date."
              >
                <TimelinePanel />
              </Section>

              <Section
                title="Cash flow"
                subtitle="Where every rupee that entered your wallet actually went."
              >
                <CashflowPanel />
              </Section>
            </>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
