/**
 * Portfolio DNA radar (§15.2) -- sector or asset-class exposure as a shape.
 *
 * Axes are scaled to the largest slice rather than to 100%, because a realistic
 * portfolio rarely puts 100% anywhere and a 0-100 axis would squash every real
 * portfolio into an unreadable dot near the centre. The tooltip and the legend
 * both state the true percentage, so the shape is a summary, not the source.
 */

import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'

import { EmptyState } from '../ui'
import AllocationBar from './AllocationBar'
import { axisProps, chartTokens, tooltipStyle } from './chartTheme'
import { formatCurrency } from '../../utils/formatters'

// A radar needs at least three axes to enclose an area. With two it degenerates
// into a line and with one into a spoke -- shapes that carry no comparative
// meaning. Below this, fall back to bars, which read fine at any count.
const MIN_RADAR_AXES = 3

export default function PortfolioRadar({ items = [], height = 300 }) {
  if (!items.length) {
    return <EmptyState title="No allocation data" description="Buy something to see your mix." />
  }

  if (items.length < MIN_RADAR_AXES) {
    return <AllocationBar items={items} height={height} />
  }

  const t = chartTokens()
  // More than eight spokes and the labels collide; group the tail so the shape
  // stays honest without becoming illegible.
  const sorted = [...items].sort((a, b) => Number(b.pct) - Number(a.pct))
  const head = sorted.slice(0, 8)
  const tail = sorted.slice(8)
  const data = head.map((i) => ({
    label: i.label,
    pct: Number(i.pct),
    value: Number(i.value),
  }))
  if (tail.length) {
    data.push({
      label: `Other (${tail.length})`,
      pct: tail.reduce((s, i) => s + Number(i.pct), 0),
      value: tail.reduce((s, i) => s + Number(i.value), 0),
    })
  }

  const max = Math.max(...data.map((d) => d.pct))
  const domainMax = Math.ceil(max / 10) * 10 || 10

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} outerRadius="72%">
          <PolarGrid stroke={t.border} />
          <PolarAngleAxis dataKey="label" tick={{ fill: t.textSecondary, fontSize: 11 }} />
          <PolarRadiusAxis
            domain={[0, domainMax]}
            angle={90}
            tick={{ ...axisProps().tick, fontSize: 10 }}
            tickFormatter={(v) => `${v}%`}
            stroke={t.border}
          />
          <Radar
            name="Share"
            dataKey="pct"
            stroke={t.accent}
            fill={t.accent}
            fillOpacity={0.28}
            isAnimationActive
          />
          <Tooltip
            {...tooltipStyle()}
            formatter={(value, _name, entry) => [
              `${Number(value).toFixed(1)}% · ${formatCurrency(entry.payload.value)}`,
              'Share',
            ]}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
