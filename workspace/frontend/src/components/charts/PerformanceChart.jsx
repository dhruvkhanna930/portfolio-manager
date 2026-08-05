import { useState } from 'react'
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { usePortfolioPerformance } from '../../hooks/useAnalytics'
import { formatCurrency, formatDate } from '../../utils/formatters'
import Skeleton from '../ui/Skeleton'
import EmptyState from '../ui/EmptyState'
import Tabs from '../ui/Tabs'

const PERIOD_TABS = [
  { key: '1W', label: '1W' },
  { key: '1M', label: '1M' },
  { key: '6M', label: '6M' },
  { key: '1Y', label: '1Y' },
  { key: '3Y', label: '3Y' },
  { key: '5Y', label: '5Y' },
  { key: 'ALL', label: 'ALL' },
]

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const point = payload[0].payload
  return (
    <div className="rounded border border-border bg-surface px-3 py-2 text-sm shadow-lg">
      <p className="text-text-secondary">{formatDate(point.date)}</p>
      <p className="font-medium tabular-nums text-text-primary">{formatCurrency(point.value)}</p>
    </div>
  )
}

export default function PerformanceChart() {
  const [period, setPeriod] = useState('1Y')
  const { data, isLoading, isFetching } = usePortfolioPerformance(period)

  const points = data?.points ?? []
  const values = points.map((p) => Number(p.value))
  const first = values[0]
  const last = values[values.length - 1]
  const change = first != null && last != null ? last - first : null
  const changePct = change != null && first ? (change / first) * 100 : null
  const isUp = change == null || change >= 0
  const lineColor = isUp ? '#16C784' : '#F6465D'

  const chartData = points.map((p) => ({ date: p.date, value: Number(p.value) }))

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-medium uppercase tracking-wide text-text-secondary">
            Portfolio Performance
          </h2>
          {!isLoading && change != null && (
            <p className={`mt-1 text-sm tabular-nums ${isUp ? 'text-positive' : 'text-negative'}`}>
              {change >= 0 ? '+' : ''}
              {formatCurrency(change)} ({changePct >= 0 ? '+' : ''}
              {changePct.toFixed(2)}%) over this period
            </p>
          )}
        </div>
        <Tabs tabs={PERIOD_TABS} value={period} onChange={setPeriod} />
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full rounded" />
      ) : chartData.length === 0 ? (
        <EmptyState
          title="No performance data yet"
          description="Buy something to start tracking portfolio value over time."
        />
      ) : (
        <div className={`h-64 w-full transition-opacity ${isFetching ? 'opacity-60' : 'opacity-100'}`}>
          <ResponsiveContainer>
            <AreaChart data={chartData} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
              <defs>
                <linearGradient id="performanceFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={lineColor} stopOpacity={0.28} />
                  <stop offset="100%" stopColor={lineColor} stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="date"
                tickFormatter={(d) => formatDate(d, { day: 'numeric', month: 'short' })}
                stroke="#5C6270"
                tick={{ fontSize: 11, fill: '#9298A5' }}
                tickLine={false}
                axisLine={false}
                minTickGap={40}
              />
              <YAxis
                domain={['auto', 'auto']}
                tickFormatter={(v) => formatCurrency(v, { compact: true })}
                stroke="#5C6270"
                tick={{ fontSize: 11, fill: '#9298A5' }}
                tickLine={false}
                axisLine={false}
                width={64}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="value"
                stroke={lineColor}
                strokeWidth={2}
                fill="url(#performanceFill)"
                isAnimationActive
                animationDuration={250}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
