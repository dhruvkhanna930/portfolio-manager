export function formatCurrency(value, { compact = false } = {}) {
  if (value == null || Number.isNaN(value)) return '—'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: compact ? 1 : 2,
    notation: compact ? 'compact' : 'standard',
  }).format(value)
}

export function formatPercent(value, { showSign = true } = {}) {
  if (value == null || Number.isNaN(value)) return '—'
  const sign = showSign && value > 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

export function formatNumber(value, options = {}) {
  if (value == null || Number.isNaN(value)) return '—'
  return new Intl.NumberFormat('en-IN', options).format(value)
}
