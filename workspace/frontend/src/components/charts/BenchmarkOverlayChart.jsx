/**
 * Benchmark comparison overlay (§15.2, data from §14.4).
 *
 * Every series is rebased to 100 at the start of the window, which is the only
 * way index levels and a portfolio value are comparable at all — the y-axis is
 * growth, not rupees, and the axis label says so.
 *
 * Assumption lines (FD, inflation) are dashed and called out in the legend, so
 * a modelled straight line can never be mistaken for fetched market data.
 */

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { EmptyState } from '../ui'
import { axisProps, chartTokens, seriesColor } from './chartTheme'
import { formatDate } from '../../utils/formatters'

export default function BenchmarkOverlayChart({ series = [], height = 340 }) {
  if (!series.length) {
    return <EmptyState title="No comparison data" description="Sync benchmarks to compare." />
  }

  const t = chartTokens()

  // Union of all dates, then fill each series by key so Recharts can align them
  // even when a benchmark trades on a day the portfolio doesn't.
  const byDate = new Map()
  series.forEach((s) => {
    s.points.forEach((p) => {
      const row = byDate.get(p.date) ?? { date: p.date }
      row[s.code] = Number(p.value)
      byDate.set(p.date, row)
    })
  })
  const data = [...byDate.values()].sort((a, b) => a.date.localeCompare(b.date))

  const colorFor = (s, i) => (s.code === 'PORTFOLIO' ? t.accent : seriesColor(i + 1))

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 4 }}>
          <CartesianGrid stroke={t.border} strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="date"
            {...axisProps()}
            minTickGap={56}
            tickFormatter={(v) => formatDate(v, { month: 'short', year: '2-digit' })}
          />
          <YAxis
            {...axisProps()}
            width={52}
            domain={['auto', 'auto']}
            label={{
              value: 'Rebased to 100',
              angle: -90,
              position: 'insideLeft',
              fill: t.textMuted,
              fontSize: 11,
            }}
          />
          <Tooltip
            contentStyle={{
              background: t.surface,
              border: `1px solid ${t.border}`,
              borderRadius: 8,
              fontSize: 12,
            }}
            labelFormatter={(v) => formatDate(v)}
            formatter={(value, name) => {
              const s = series.find((x) => x.code === name)
              return [Number(value).toFixed(1), s ? s.label : name]
            }}
          />
          <Legend
            wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
            formatter={(value) => {
              const s = series.find((x) => x.code === value)
              if (!s) return value
              return (
                <span style={{ color: t.textSecondary }}>
                  {s.label}
                  {s.is_assumption && <span style={{ color: t.warning }}> (assumption)</span>}
                </span>
              )
            }}
          />
          {series.map((s, i) => (
            <Line
              key={s.code}
              type="monotone"
              dataKey={s.code}
              name={s.code}
              stroke={colorFor(s, i)}
              strokeWidth={s.code === 'PORTFOLIO' ? 2.4 : 1.6}
              strokeDasharray={s.is_assumption ? '5 4' : undefined}
              dot={false}
              connectNulls
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
