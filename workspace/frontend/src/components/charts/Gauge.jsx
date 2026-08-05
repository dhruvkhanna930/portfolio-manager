/**
 * Health Score dial (§15.2), drawn with d3-shape arcs.
 *
 * A 240-degree sweep rather than a full circle: the gap at the bottom gives the
 * needle an unambiguous "empty" end, so a score of 0 and a score of 100 can't
 * be confused at a glance the way they can on a closed ring.
 *
 * The numeric score is printed in the middle at full size -- the arc is the
 * decoration, the number is the fact.
 */

import { useEffect, useMemo, useRef, useState } from 'react'
import { arc as d3arc } from 'd3-shape'
import { animate } from 'framer-motion'

import { chartTokens } from './chartTheme'

const START_ANGLE = -Math.PI * (2 / 3)
const END_ANGLE = Math.PI * (2 / 3)
const SWEEP = END_ANGLE - START_ANGLE

export default function Gauge({ value, max = 100, size = 200, label, bandLabel, tone = 'accent' }) {
  const [display, setDisplay] = useState(0)
  const prefersReduced = useRef(
    typeof window !== 'undefined' &&
      window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  )

  useEffect(() => {
    const target = value ?? 0
    if (prefersReduced.current) {
      setDisplay(target)
      return undefined
    }
    const controls = animate(0, target, {
      duration: 1.0,
      ease: 'easeOut',
      onUpdate: setDisplay,
    })
    return () => controls.stop()
  }, [value])

  const t = chartTokens()
  const toneColor = tone === 'positive' ? t.positive : tone === 'negative' ? t.negative : t.accent

  const radius = size / 2
  const thickness = Math.max(12, size * 0.085)
  const { trackPath, valuePath, needle } = useMemo(() => {
    const builder = d3arc()
      .innerRadius(radius - thickness)
      .outerRadius(radius)
      .cornerRadius(thickness / 2)

    const frac = Math.max(0, Math.min(1, (display ?? 0) / max))
    const valueEnd = START_ANGLE + SWEEP * frac
    const angle = valueEnd - Math.PI / 2

    // A short tick riding the arc's leading edge rather than a full-radius
    // needle: a needle from the hub would run straight through the score text
    // in the middle, which is the one thing on this dial that must stay legible.
    const inner = radius - thickness - 3
    const outer = radius + 3
    return {
      trackPath: builder({ startAngle: START_ANGLE, endAngle: END_ANGLE }),
      valuePath: builder({ startAngle: START_ANGLE, endAngle: valueEnd }),
      needle: {
        x1: Math.cos(angle) * inner,
        y1: Math.sin(angle) * inner,
        x2: Math.cos(angle) * outer,
        y2: Math.sin(angle) * outer,
      },
    }
  }, [display, max, radius, thickness])

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size * 0.78} viewBox={`${-radius} ${-radius} ${size} ${size * 0.78}`}>
        <path d={trackPath} fill={t.border} />
        <path d={valuePath} fill={toneColor} opacity={0.9} />
        <line
          x1={needle.x1}
          y1={needle.y1}
          x2={needle.x2}
          y2={needle.y2}
          stroke={t.textPrimary}
          strokeWidth={2}
          strokeLinecap="round"
          opacity={0.85}
        />
        <text
          x={0}
          y={2}
          textAnchor="middle"
          dominantBaseline="middle"
          fill={t.textPrimary}
          style={{ fontSize: size * 0.24, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}
        >
          {Math.round(display ?? 0)}
        </text>
        <text
          x={0}
          y={size * 0.17}
          textAnchor="middle"
          fill={t.textMuted}
          style={{ fontSize: size * 0.07 }}
        >
          / {max}
        </text>
      </svg>

      {(label || bandLabel) && (
        <div className="-mt-1 text-center">
          {bandLabel && (
            <p className="text-sm font-medium" style={{ color: toneColor }}>
              {bandLabel}
            </p>
          )}
          {label && <p className="mt-0.5 text-xs text-text-muted">{label}</p>}
        </div>
      )}
    </div>
  )
}
