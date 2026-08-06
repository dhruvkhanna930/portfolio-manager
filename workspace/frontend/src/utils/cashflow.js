/**
 * Shapes wallet_ledger + transactions into Sankey / Waterfall inputs (§15.2).
 *
 * Pure functions over data the API already returns -- no new numbers are
 * invented here, and the totals are just the ledger re-grouped. The ledger is
 * the source of truth for cash (§6.10), so every figure below traces back to a
 * signed ledger row.
 */

import { seriesColor, token } from '../components/charts/chartTheme'

function cleanSymbol(symbol) {
  return String(symbol ?? '').replace(/\.(NS|BO)$/, '')
}

/** Sum of the ledger, grouped by entry_type, as positive magnitudes. */
export function summariseLedger(entries = []) {
  const totals = { DEPOSIT: 0, WITHDRAWAL: 0, BUY: 0, SELL: 0, DIVIDEND: 0, FEE: 0 }
  for (const entry of entries) {
    const amount = Number(entry.amount)
    if (Number.isNaN(amount)) continue
    if (entry.entry_type in totals) totals[entry.entry_type] += Math.abs(amount)
  }
  return totals
}

/**
 * Sankey graph: money in (deposits, sales, dividends) → wallet → money out
 * (purchases per asset, withdrawals) and whatever is still sitting as cash.
 *
 * Purchases are broken out per asset by joining ledger rows to transactions on
 * transaction_id. Ledger rows we can't attribute fall into a single "Other
 * purchases" bucket rather than being silently dropped.
 */
export function buildCashflowSankey({ entries = [], transactions = [], balance = 0 }) {
  const totals = summariseLedger(entries)
  const txnById = new Map(transactions.map((t) => [t.transaction_id, t]))

  const buysByAsset = new Map()
  let unattributedBuys = 0
  for (const entry of entries) {
    if (entry.entry_type !== 'BUY') continue
    const amount = Math.abs(Number(entry.amount))
    const txn = entry.transaction_id != null ? txnById.get(entry.transaction_id) : null
    const symbol = txn?.asset?.symbol ?? txn?.symbol
    if (!symbol) {
      unattributedBuys += amount
      continue
    }
    const key = cleanSymbol(symbol)
    buysByAsset.set(key, (buysByAsset.get(key) ?? 0) + amount)
  }

  const inflow = totals.DEPOSIT + totals.SELL + totals.DIVIDEND
  if (inflow <= 0) return { nodes: [], links: [] }

  const positive = token('--positive', '#16C784')
  const negative = token('--negative', '#F6465D')
  const accent = token('--accent', '#22D3A6')
  const muted = token('--text-muted', '#7A808E')

  const nodes = [{ id: 'wallet', label: 'Wallet', color: accent }]
  const links = []

  const addSource = (id, label, value, color) => {
    if (value <= 0) return
    nodes.push({ id, label, color })
    links.push({ source: id, target: 'wallet', value, color })
  }
  addSource('deposits', 'Deposits', totals.DEPOSIT, positive)
  addSource('sales', 'Sale proceeds', totals.SELL, positive)
  addSource('dividends', 'Dividends', totals.DIVIDEND, positive)

  const addTarget = (id, label, value, color) => {
    if (value <= 0) return
    nodes.push({ id, label, color })
    links.push({ source: 'wallet', target: id, value, color })
  }

  // Cap the number of per-asset nodes so the diagram stays readable; the tail
  // is grouped rather than hidden.
  const sortedBuys = [...buysByAsset.entries()].sort((a, b) => b[1] - a[1])
  const head = sortedBuys.slice(0, 8)
  const tail = sortedBuys.slice(8)
  head.forEach(([symbol, value], i) => {
    addTarget(`buy-${symbol}`, symbol, value, seriesColor(i))
  })
  const tailTotal = tail.reduce((sum, [, value]) => sum + value, 0) + unattributedBuys
  addTarget('buy-other', tail.length ? `Other (${tail.length})` : 'Other purchases', tailTotal, muted)

  addTarget('withdrawals', 'Withdrawals', totals.WITHDRAWAL, negative)
  addTarget('fees', 'Fees', totals.FEE, negative)
  addTarget('cash', 'Cash on hand', Math.max(0, Number(balance)), muted)

  return { nodes, links }
}

/** Waterfall steps: each cash movement as a delta, ending on the real balance. */
export function buildCashflowWaterfall({ entries = [], balance = 0 }) {
  const totals = summariseLedger(entries)
  const steps = [
    { label: 'Deposits', amount: totals.DEPOSIT },
    { label: 'Sales', amount: totals.SELL },
    { label: 'Dividends', amount: totals.DIVIDEND },
    { label: 'Purchases', amount: -totals.BUY },
    { label: 'Withdrawals', amount: -totals.WITHDRAWAL },
    { label: 'Fees', amount: -totals.FEE },
  ].filter((step) => step.amount !== 0)

  if (!steps.length) return []
  return [...steps, { label: 'Balance', amount: Number(balance), isTotal: true }]
}
