/**
 * Shared chart plumbing so every §15.2 chart reads from the §8.1 tokens rather
 * than hard-coding hexes. One place to change the palette, and charts inherit
 * the theme instead of drifting from it.
 */

export function token(name, fallback) {
  if (typeof window === 'undefined') return fallback
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value || fallback
}

export const chartTokens = () => ({
  accent: token('--accent', '#22D3A6'),
  positive: token('--positive', '#16C784'),
  negative: token('--negative', '#F6465D'),
  warning: token('--warning', '#F0B90B'),
  border: token('--border', '#22252C'),
  surface: token('--surface', '#12141A'),
  surfaceHover: token('--surface-hover', '#1A1D24'),
  textPrimary: token('--text-primary', '#F5F6FA'),
  textSecondary: token('--text-secondary', '#9298A5'),
  textMuted: token('--text-muted', '#7A808E'),
})

/** Categorical series colours — accent-led, distinguishable on a dark ground. */
export const SERIES_COLORS = [
  '#22D3A6',
  '#6366F1',
  '#F0B90B',
  '#EC4899',
  '#38BDF8',
  '#A78BFA',
  '#FB923C',
  '#4ADE80',
  '#F472B6',
  '#2DD4BF',
]

export const seriesColor = (index) => SERIES_COLORS[index % SERIES_COLORS.length]

/** Recharts tooltip styling, matched to Card. */
export const tooltipStyle = () => {
  const t = chartTokens()
  return {
    contentStyle: {
      background: t.surface,
      border: `1px solid ${t.border}`,
      borderRadius: 8,
      fontSize: 12,
      color: t.textPrimary,
      boxShadow: '0 8px 24px rgba(0,0,0,0.45)',
    },
    labelStyle: { color: t.textSecondary, marginBottom: 4 },
    itemStyle: { color: t.textPrimary },
  }
}

export const axisProps = () => {
  const t = chartTokens()
  return {
    stroke: t.border,
    tick: { fill: t.textMuted, fontSize: 11 },
    tickLine: false,
  }
}
