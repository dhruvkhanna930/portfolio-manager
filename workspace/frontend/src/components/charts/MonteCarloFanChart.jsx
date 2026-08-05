/**
 * Monte Carlo percentile fan (§15.2, data from §14.6).
 *
 * Drawn as two stacked areas so the band between p10 and p90 is filled without
 * a fake "lower bound" series: the base area is the p10 line rendered fully
 * transparent, and the visible band is (p90 - p10) stacked on top of it. That
 * keeps the y-axis reading true values rather than offsets.
 *
 * The median is a line, not a fill, because it is a single path among many --
 * filling to it would suggest a certainty the simulation does not have.
 */

import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { EmptyState } from '../ui'
import { axisProps, chartTokens, tooltipStyle } from './chartTheme'
import { formatCurrency } from '../../utils/formatters'

export default function MonteCarloFanChart({ series = [], height = 320 }) {
  if (!series.length) {
    return <EmptyState title="No simulation yet" description="Run a projection to see the range." />
  }

  const t = chartTokens()
  const data = series.map((s) => ({
    day: s.day,
    p10: Number(s.p10),
    p50: Number(s.p50),
    p90: Number(s.p90),
    band: Number(s.p90) - Number(s.p10),
  }))

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 8, right: 12, bottom: 18, left: 4 }}>
          <defs>
            <linearGradient id="mcBand" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={t.accent} stopOpacity={0.30} />
              <stop offset="100%" stopColor={t.accent} stopOpacity={0.10} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke={t.border} strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="day"
            {...axisProps()}
            minTickGap={48}
            // Trading days, not calendar dates: the bootstrap resamples daily
            // returns, so there is no weekend/holiday calendar to map onto.
            label={{
              value: 'Trading days from today',
              position: 'insideBottom',
              offset: -2,
              fill: t.textMuted,
              fontSize: 11,
            }}
          />
          <YAxis
            {...axisProps()}
            width={72}
            domain={['auto', 'auto']}
            tickFormatter={(v) => formatCurrency(v, { compact: true })}
          />
          <Tooltip
            {...tooltipStyle()}
            content={({ active, payload, label }) => {
              if (!active || !payload?.length) return null
              const d = payload[0].payload
              return (
                <div className="rounded border border-border bg-surface p-2.5 text-xs shadow-lg">
                  <p className="text-text-secondary">Day {label}</p>
                  <p className="mt-1.5 tabular-nums text-text-primary">
                    Optimistic (p90) {formatCurrency(d.p90)}
                  </p>
                  <p className="tabular-nums text-accent">Median (p50) {formatCurrency(d.p50)}</p>
                  <p className="tabular-nums text-text-primary">
                    Pessimistic (p10) {formatCurrency(d.p10)}
                  </p>
                </div>
              )
            }}
          />
          {/* Invisible pedestal so the band sits at its true y position. */}
          <Area
            type="monotone"
            dataKey="p10"
            stackId="fan"
            stroke="none"
            fill="transparent"
            isAnimationActive={false}
          />
          <Area
            type="monotone"
            dataKey="band"
            stackId="fan"
            stroke="none"
            fill="url(#mcBand)"
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="p50"
            stroke={t.accent}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
