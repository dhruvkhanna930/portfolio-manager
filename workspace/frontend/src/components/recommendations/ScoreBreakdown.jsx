/**
 * Stacked contribution bar for one recommendation.
 *
 * Shows what each component actually contributed to the final score --
 * component value x its weight -- rather than the component values alone. A
 * factor scoring 90 on a 0.15 weight matters less than one scoring 60 on 0.40,
 * and a bar of raw values would imply the opposite.
 */

import { chartTokens, seriesColor } from '../charts/chartTheme'

const LABELS = {
  fit: 'Fit',
  momentum: 'Momentum',
  sentiment: 'News',
  ml: 'Model',
}

const ORDER = ['fit', 'momentum', 'sentiment', 'ml']

export default function ScoreBreakdown({ components, weights, finalScore }) {
  const t = chartTokens()

  const parts = ORDER.map((key, index) => {
    const value = components?.[key]
    const weight = weights?.[key]
    if (value == null || weight == null) return null
    return {
      key,
      label: LABELS[key],
      value,
      weight,
      contribution: value * weight,
      color: seriesColor(index),
    }
  }).filter(Boolean)

  if (!parts.length) {
    return <p className="text-xs text-text-muted">No scored factors available.</p>
  }

  const total = parts.reduce((sum, p) => sum + p.contribution, 0)

  return (
    <div className="space-y-2">
      <div
        className="flex h-2 w-full overflow-hidden rounded-full"
        style={{ background: t.surfaceHover }}
        role="img"
        aria-label={`Score ${finalScore} out of 100, built from ${parts
          .map((p) => `${p.label} ${Math.round(p.value)}`)
          .join(', ')}`}
      >
        {parts.map((p) => (
          <div
            key={p.key}
            style={{
              width: `${total > 0 ? (p.contribution / total) * 100 : 0}%`,
              background: p.color,
            }}
            title={`${p.label}: scored ${p.value.toFixed(0)}/100, weighted ${(p.weight * 100).toFixed(0)}%`}
          />
        ))}
      </div>

      <div className="flex flex-wrap gap-x-3 gap-y-1">
        {parts.map((p) => (
          <span key={p.key} className="flex items-center gap-1.5 text-[11px] text-text-secondary">
            <span
              className="h-2 w-2 shrink-0 rounded-full"
              style={{ background: p.color }}
              aria-hidden="true"
            />
            {p.label}
            <span className="tabular-nums text-text-muted">
              {p.value.toFixed(0)} × {(p.weight * 100).toFixed(0)}%
            </span>
          </span>
        ))}
      </div>
    </div>
  )
}
