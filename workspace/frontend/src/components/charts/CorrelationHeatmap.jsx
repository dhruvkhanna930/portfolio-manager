/**
 * Correlation heatmap (§15.2, data from §14.2).
 *
 * Diverging red/neutral/green scale centred on 0 and locked to the true [-1, 1]
 * domain, not to the data's own min/max. Auto-scaling here would make a
 * portfolio whose correlations all sit between 0.6 and 0.8 look like it spans
 * the full range of possible relationships, which is the opposite of the truth.
 *
 * Cells with too few overlapping observations render as an explicit dash and a
 * hatched background -- distinguishable from a genuine zero at a glance.
 */

import { useState } from 'react'
import { scaleDiverging } from 'd3-scale'
import { interpolateRgb } from 'd3-interpolate'

import { EmptyState } from '../ui'
import { chartTokens } from './chartTheme'

function cleanSymbol(symbol) {
  return String(symbol ?? '').replace(/\.(NS|BO)$/, '')
}

export default function CorrelationHeatmap({ assets = [], matrix = [] }) {
  const [hover, setHover] = useState(null)

  if (!assets.length) {
    return (
      <EmptyState
        title="Nothing to correlate"
        description="You need at least two holdings with overlapping price history."
      />
    )
  }

  const t = chartTokens()
  // Negative correlation is the diversifying one, so it gets the "good" colour;
  // this is a deliberate semantic choice, and the legend below spells it out.
  const color = scaleDiverging()
    .domain([-1, 0, 1])
    .interpolator((x) =>
      x < 0.5
        ? interpolateRgb(t.positive, t.surface)(x * 2)
        : interpolateRgb(t.surface, t.negative)((x - 0.5) * 2)
    )

  const labels = assets.map((a) => cleanSymbol(a.symbol))

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto">
        <table className="border-separate" style={{ borderSpacing: 2 }}>
          <thead>
            <tr>
              <th className="sticky left-0 z-10 bg-surface" />
              {labels.map((label, j) => (
                <th
                  key={label}
                  className={`px-1 pb-1 text-[10px] font-medium ${
                    hover?.j === j ? 'text-text-primary' : 'text-text-secondary'
                  }`}
                  style={{ minWidth: 52 }}
                >
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row, i) => (
              <tr key={labels[i]}>
                <th
                  className={`sticky left-0 z-10 bg-surface pr-2 text-right text-[10px] font-medium ${
                    hover?.i === i ? 'text-text-primary' : 'text-text-secondary'
                  }`}
                >
                  {labels[i]}
                </th>
                {row.map((value, j) => {
                  const isNull = value == null
                  const active = hover && (hover.i === i || hover.j === j)
                  return (
                    <td
                      key={`${i}-${j}`}
                      onMouseEnter={() => setHover({ i, j, value })}
                      onMouseLeave={() => setHover(null)}
                      title={
                        isNull
                          ? `${labels[i]} vs ${labels[j]}: too few overlapping observations`
                          : `${labels[i]} vs ${labels[j]}: ${value.toFixed(2)}`
                      }
                      className="h-9 cursor-default rounded text-center text-[11px] tabular-nums transition-opacity"
                      style={{
                        minWidth: 52,
                        background: isNull ? undefined : color(value),
                        backgroundImage: isNull
                          ? `repeating-linear-gradient(45deg, ${t.border} 0 4px, transparent 4px 8px)`
                          : undefined,
                        color: isNull ? t.textMuted : t.textPrimary,
                        opacity: hover && !active ? 0.35 : 1,
                        outline: i === j ? `1px solid ${t.border}` : undefined,
                      }}
                    >
                      {isNull ? '—' : value.toFixed(2)}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-text-muted">
        <span className="flex items-center gap-1.5">
          <span
            className="h-3 w-16 rounded"
            style={{
              background: `linear-gradient(to right, ${t.positive}, ${t.surface}, ${t.negative})`,
            }}
          />
          −1 (moves opposite) → 0 → +1 (moves together)
        </span>
        <span className="flex items-center gap-1.5">
          <span
            className="h-3 w-3 rounded"
            style={{
              backgroundImage: `repeating-linear-gradient(45deg, ${t.border} 0 4px, transparent 4px 8px)`,
            }}
          />
          too few overlapping days to measure
        </span>
      </div>
    </div>
  )
}
