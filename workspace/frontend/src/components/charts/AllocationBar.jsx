import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { formatCurrency, formatPercent } from '../../utils/formatters'
import Skeleton from '../ui/Skeleton'
import EmptyState from '../ui/EmptyState'

const PALETTE = ['#22D3A6', '#5B8DEF', '#F0B90B', '#A78BFA', '#F6465D', '#2DD4BF', '#FB923C', '#818CF8']

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const item = payload[0].payload
  return (
    <div className="rounded border border-border bg-surface px-3 py-2 text-sm shadow-lg">
      <p className="font-medium text-text-primary">{item.label}</p>
      <p className="text-text-secondary">
        {formatCurrency(item.value)} · {formatPercent(item.pct, { showSign: false })}
      </p>
    </div>
  )
}

export default function AllocationBar({ items = [], loading = false, height = 220 }) {
  if (loading) {
    return (
      <div className="space-y-2" style={{ height }}>
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-6 w-full rounded" />
        ))}
      </div>
    )
  }

  if (items.length === 0) {
    return <EmptyState title="No sector data yet" description="Add a priced holding to see the breakdown." />
  }

  const data = items
    .map((item, index) => ({
      label: item.label,
      value: Number(item.value),
      pct: Number(item.pct),
      color: PALETTE[index % PALETTE.length],
    }))
    .sort((a, b) => b.value - a.value)

  return (
    <div style={{ height }}>
      <ResponsiveContainer>
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 16, left: 0, bottom: 0 }}>
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="label"
            width={110}
            stroke="#5C6270"
            tick={{ fontSize: 11, fill: '#9298A5' }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'transparent' }} />
          <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={16}>
            {data.map((entry) => (
              <Cell key={entry.label} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
