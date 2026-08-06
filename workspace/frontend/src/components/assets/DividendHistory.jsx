/**
 * Dividend history (§15.4).
 *
 * Strictly the DIVIDEND transactions the user recorded for this asset — not
 * yfinance's corporate-action feed. Those are different facts: one is what this
 * portfolio actually received, the other is what the company declared per share
 * whether or not it was held. Mixing them would produce a total that matches
 * neither, so this panel is explicit about which it shows.
 */

import { useMemo } from 'react'

import { formatCurrency, formatDate } from '../../utils/formatters'

export default function DividendHistory({ assetId, transactions = [] }) {
  const dividends = useMemo(
    () =>
      transactions
        .filter((t) => t.txn_type === 'DIVIDEND' && t.asset_id === assetId)
        .map((t) => ({
          id: t.transaction_id,
          date: t.txn_date,
          // A DIVIDEND row books quantity × price as the cash received (§6.10).
          amount: Number(t.quantity) * Number(t.price),
          perUnit: Number(t.price),
          units: Number(t.quantity),
        }))
        .sort((a, b) => b.date.localeCompare(a.date)),
    [assetId, transactions]
  )

  if (!dividends.length) return null

  const total = dividends.reduce((sum, d) => sum + d.amount, 0)

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-sm text-text-secondary">
          {dividends.length} payment{dividends.length > 1 ? 's' : ''} recorded
        </p>
        <p className="text-sm">
          <span className="text-text-secondary">Total received </span>
          <span className="font-semibold tabular-nums text-positive">{formatCurrency(total)}</span>
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[22rem] text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase text-text-secondary">
              <th className="py-2 pr-4 font-medium">Date</th>
              <th className="py-2 pr-4 text-right font-medium">Units</th>
              <th className="py-2 pr-4 text-right font-medium">Per unit</th>
              <th className="py-2 text-right font-medium">Amount</th>
            </tr>
          </thead>
          <tbody>
            {dividends.map((d) => (
              <tr key={d.id} className="border-b border-border/50">
                <td className="py-2 pr-4 text-text-secondary">{formatDate(d.date)}</td>
                <td className="py-2 pr-4 text-right tabular-nums text-text-secondary">{d.units}</td>
                <td className="py-2 pr-4 text-right tabular-nums text-text-secondary">
                  {formatCurrency(d.perUnit)}
                </td>
                <td className="py-2 text-right tabular-nums text-positive">
                  {formatCurrency(d.amount)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-text-muted">
        Dividends you recorded against this holding, from your own transaction log — not the
        issuer&apos;s full declared payout history.
      </p>
    </div>
  )
}
