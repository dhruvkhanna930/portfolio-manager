import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
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

export default function AllocationDonut({ items = [], loading = false }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{ height: 220 }}>
        <Skeleton className="h-44 w-44 rounded-full" />
      </div>
    )
  }

  if (items.length === 0) {
    return <EmptyState title="No allocation data yet" description="Add a priced holding to see the breakdown." />
  }

  const data = items.map((item, index) => ({
    label: item.label,
    value: Number(item.value),
    pct: Number(item.pct),
    color: PALETTE[index % PALETTE.length],
  }))

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
      <div style={{ width: 200, height: 200 }} className="mx-auto shrink-0 sm:mx-0">
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="label"
              innerRadius={58}
              outerRadius={94}
              paddingAngle={2}
              stroke="none"
            >
              {data.map((entry) => (
                <Cell key={entry.label} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="flex-1 space-y-2">
        {data.map((item) => (
          <li key={item.label} className="flex items-center justify-between gap-3 text-sm">
            <span className="flex items-center gap-2 text-text-secondary">
              <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: item.color }} />
              {item.label}
            </span>
            <span className="shrink-0 tabular-nums text-text-primary">
              {formatPercent(item.pct, { showSign: false })}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
