/**
 * Cash-flow waterfall (§15.2).
 *
 * Same stacked-transparent-base trick as the fan chart: an invisible bar lifts
 * each visible bar to where the running total actually sits, so bar *length*
 * encodes the size of each flow and bar *position* encodes the running balance.
 *
 * The final bar is a total, drawn from zero and visually separated, because a
 * total is a different kind of quantity from the deltas that produced it.
 */

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { EmptyState } from '../ui'
import { axisProps, chartTokens, tooltipStyle } from './chartTheme'
import { formatCurrency } from '../../utils/formatters'

export default function WaterfallChart({ steps = [], height = 300 }) {
  if (!steps.length) {
    return <EmptyState title="No cash flow yet" description="Deposit funds to see the breakdown." />
  }

  const t = chartTokens()
  let running = 0
  const data = steps.map((step) => {
    const amount = Number(step.amount)
    if (step.isTotal) {
      return { label: step.label, base: 0, bar: running, amount: running, isTotal: true }
    }
    const base = amount >= 0 ? running : running + amount
    running += amount
    return { label: step.label, base, bar: Math.abs(amount), amount, isTotal: false }
  })

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 4 }}>
          <CartesianGrid stroke={t.border} strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="label" {...axisProps()} interval={0} tick={{ ...axisProps().tick, fontSize: 10 }} />
          <YAxis
            {...axisProps()}
            width={72}
            tickFormatter={(v) => formatCurrency(v, { compact: true })}
          />
          <Tooltip
            {...tooltipStyle()}
            cursor={{ fill: 'rgba(255,255,255,0.04)' }}
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null
              const d = payload[0].payload
              return (
                <div className="rounded border border-border bg-surface p-2.5 text-xs shadow-lg">
                  <p className="font-medium text-text-primary">{d.label}</p>
                  <p
                    className={`mt-1 tabular-nums ${
                      d.isTotal ? 'text-text-primary' : d.amount >= 0 ? 'text-positive' : 'text-negative'
                    }`}
                  >
                    {d.isTotal ? '' : d.amount >= 0 ? '+' : ''}
                    {formatCurrency(d.amount)}
                  </p>
                </div>
              )
            }}
          />
          <Bar dataKey="base" stackId="w" fill="transparent" isAnimationActive={false} />
          <Bar dataKey="bar" stackId="w" radius={[3, 3, 0, 0]}>
            {data.map((d, i) => (
              <Cell
                key={i}
                fill={d.isTotal ? t.accent : d.amount >= 0 ? t.positive : t.negative}
                fillOpacity={d.isTotal ? 0.9 : 0.75}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
