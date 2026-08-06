/**
 * GitHub-style activity calendar (§15.2 / §15 item 3).
 *
 * One cell per day, weeks as columns. Intensity is bucketed rather than
 * continuous: with a handful of transactions a linear scale would render almost
 * everything at the same barely-visible alpha, and the point of this chart is
 * spotting *when* activity clustered, not comparing day 3 to day 4.
 */

import { useMemo, useState } from 'react'
import { timeDay, timeSunday } from 'd3-time'

import { chartTokens } from './chartTheme'
import { formatDate } from '../../utils/formatters'

const CELL = 11
const GAP = 3
const DAY_LABELS = ['', 'Mon', '', 'Wed', '', 'Fri', '']

function isoDate(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export default function CalendarHeatmap({ events = [], months = 12, onSelectDate }) {
  const [hover, setHover] = useState(null)
  const t = chartTokens()

  const { weeks, byDate, maxCount, monthMarks } = useMemo(() => {
    const counts = new Map()
    for (const event of events) {
      const key = String(event.date).slice(0, 10)
      const existing = counts.get(key) ?? { count: 0, buys: 0, sells: 0, items: [] }
      existing.count += 1
      if (event.type === 'BUY') existing.buys += 1
      else if (event.type === 'SELL') existing.sells += 1
      existing.items.push(event)
      counts.set(key, existing)
    }

    const end = timeDay.floor(new Date())
    const start = timeSunday.floor(timeDay.offset(end, -months * 30))
    const days = timeDay.range(start, timeDay.offset(end, 1))

    const cols = []
    let current = []
    const marks = []
    let lastMonth = null
    for (const day of days) {
      if (day.getDay() === 0 && current.length) {
        cols.push(current)
        current = []
      }
      if (!current.length) {
        const month = day.getMonth()
        if (month !== lastMonth) {
          marks.push({ col: cols.length, label: day.toLocaleString('en-IN', { month: 'short' }) })
          lastMonth = month
        }
      }
      current.push(day)
    }
    if (current.length) cols.push(current)

    return {
      weeks: cols,
      byDate: counts,
      maxCount: Math.max(1, ...[...counts.values()].map((c) => c.count)),
      monthMarks: marks,
    }
  }, [events, months])

  const bucketColor = (count) => {
    if (!count) return t.border
    const step = Math.ceil((count / maxCount) * 4)
    return { 1: 0.3, 2: 0.5, 3: 0.72, 4: 1 }[Math.max(1, Math.min(4, step))]
  }

  const width = weeks.length * (CELL + GAP) + 34
  const height = 7 * (CELL + GAP) + 22

  return (
    <div className="space-y-2">
      <div className="overflow-x-auto pb-1">
        <svg width={width} height={height} role="img" aria-label="Transaction activity by day">
          {monthMarks.map((mark) => (
            <text
              key={`${mark.col}-${mark.label}`}
              x={34 + mark.col * (CELL + GAP)}
              y={9}
              fill={t.textMuted}
              style={{ fontSize: 9 }}
            >
              {mark.label}
            </text>
          ))}
          {DAY_LABELS.map((label, i) =>
            label ? (
              <text
                key={label}
                x={0}
                y={22 + i * (CELL + GAP) + CELL - 2}
                fill={t.textMuted}
                style={{ fontSize: 9 }}
              >
                {label}
              </text>
            ) : null
          )}
          {weeks.map((week, wi) =>
            week.map((day) => {
              const key = isoDate(day)
              const entry = byDate.get(key)
              const count = entry?.count ?? 0
              const alpha = bucketColor(count)
              const isHover = hover?.key === key
              return (
                <rect
                  key={key}
                  x={34 + wi * (CELL + GAP)}
                  y={22 + day.getDay() * (CELL + GAP)}
                  width={CELL}
                  height={CELL}
                  rx={2}
                  fill={count ? t.accent : t.border}
                  fillOpacity={count ? alpha : 0.5}
                  stroke={isHover ? t.textPrimary : 'none'}
                  strokeWidth={isHover ? 1 : 0}
                  style={{ cursor: count || onSelectDate ? 'pointer' : 'default' }}
                  onMouseEnter={() => setHover({ key, entry, day })}
                  onMouseLeave={() => setHover(null)}
                  onClick={() => onSelectDate?.(key)}
                />
              )
            })
          )}
        </svg>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-text-muted">
        <span className="min-h-[1rem]">
          {hover ? (
            hover.entry ? (
              <>
                <span className="text-text-primary">{formatDate(hover.key)}</span>
                {' — '}
                {hover.entry.buys > 0 && `${hover.entry.buys} buy${hover.entry.buys > 1 ? 's' : ''}`}
                {hover.entry.buys > 0 && hover.entry.sells > 0 && ', '}
                {hover.entry.sells > 0 &&
                  `${hover.entry.sells} sell${hover.entry.sells > 1 ? 's' : ''}`}
              </>
            ) : (
              <>
                <span className="text-text-secondary">{formatDate(hover.key)}</span> — no activity
              </>
            )
          ) : (
            'Hover a day for detail.'
          )}
        </span>
        <span className="flex items-center gap-1.5">
          Less
          <span className="h-2.5 w-2.5 rounded-sm" style={{ background: t.border, opacity: 0.5 }} />
          {[0.3, 0.5, 0.72, 1].map((a) => (
            <span
              key={a}
              className="h-2.5 w-2.5 rounded-sm"
              style={{ background: t.accent, opacity: a }}
            />
          ))}
          More
        </span>
      </div>
    </div>
  )
}
