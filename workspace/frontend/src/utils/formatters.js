export function formatCurrency(value, { compact = false } = {}) {
  if (value == null) return '—'
  const num = Number(value)
  if (Number.isNaN(num)) return '—'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: compact ? 1 : 2,
    notation: compact ? 'compact' : 'standard',
  }).format(num)
}

export function formatPercent(value, { showSign = true } = {}) {
  if (value == null) return '—'
  const num = Number(value)
  if (Number.isNaN(num)) return '—'
  const sign = showSign && num > 0 ? '+' : ''
  return `${sign}${num.toFixed(2)}%`
}

export function formatNumber(value, options = {}) {
  if (value == null) return '—'
  const num = Number(value)
  if (Number.isNaN(num)) return '—'
  return new Intl.NumberFormat('en-IN', options).format(num)
}

export function formatDate(value, options = { day: 'numeric', month: 'short', year: 'numeric' }) {
  if (!value) return '—'
  const d = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(d.getTime())) return '—'
  return new Intl.DateTimeFormat('en-IN', options).format(d)
}
