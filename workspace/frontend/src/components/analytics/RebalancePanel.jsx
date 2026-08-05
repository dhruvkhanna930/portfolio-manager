import { useMemo, useState } from 'react'
import { Scale } from 'lucide-react'

import { Button, Skeleton } from '../ui'
import { useHoldings } from '../../hooks/useHoldings'
import { useRebalancePreview } from '../../hooks/useAdvancedAnalytics'
import { formatCurrency } from '../../utils/formatters'

function MetricRow({ label, current, hypothetical, format }) {
  const fmt = (v) => (v == null ? '—' : format(v))
  const delta = current != null && hypothetical != null ? hypothetical - current : null
  return (
    <tr className="border-b border-border/50">
      <td className="py-2 pr-4 text-text-secondary">{label}</td>
      <td className="py-2 pr-4 text-right tabular-nums text-text-primary">{fmt(current)}</td>
      <td className="py-2 pr-4 text-right tabular-nums text-text-primary">{fmt(hypothetical)}</td>
      <td
        className={`py-2 text-right tabular-nums ${
          delta == null ? 'text-text-muted' : delta === 0 ? 'text-text-muted' : delta > 0 ? 'text-positive' : 'text-negative'
        }`}
      >
        {delta == null ? '—' : `${delta > 0 ? '+' : ''}${format(delta)}`}
      </td>
    </tr>
  )
}

export default function RebalancePanel({ period = '1Y' }) {
  const { data: holdings = [], isLoading } = useHoldings()
  const preview = useRebalancePreview()
  const [weights, setWeights] = useState({})

  // Start from the current allocation so the user edits from where they are.
  const currentWeights = useMemo(() => {
    const total = holdings.reduce((sum, h) => sum + Number(h.current_value ?? 0), 0)
    if (!total) return {}
    return Object.fromEntries(
      holdings.map((h) => [h.asset_id, ((Number(h.current_value ?? 0) / total) * 100).toFixed(1)])
    )
  }, [holdings])

  const effective = Object.keys(weights).length ? weights : currentWeights
  const totalPct = Object.values(effective).reduce((sum, v) => sum + (Number(v) || 0), 0)
  const balanced = Math.abs(totalPct - 100) <= 1

  const setEqualWeight = () => {
    const each = (100 / holdings.length).toFixed(1)
    setWeights(Object.fromEntries(holdings.map((h) => [h.asset_id, each])))
  }

  const run = () => {
    // The API takes fractions; the UI collects percentages because that's what
    // people think in.
    const targetWeights = Object.fromEntries(
      Object.entries(effective).map(([assetId, pct]) => [assetId, (Number(pct) || 0) / 100])
    )
    preview.mutate({ targetWeights, period })
  }

  if (isLoading) return <Skeleton className="h-64 w-full rounded" />
  if (!holdings.length) return <p className="text-sm text-text-secondary">No holdings to rebalance.</p>

  const result = preview.data

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        {holdings.map((holding) => (
          <div key={holding.asset_id} className="flex items-center gap-3">
            <span className="min-w-0 flex-1 truncate text-sm text-text-primary" title={holding.asset?.name}>
              {holding.asset?.symbol?.replace(/\.(NS|BO)$/, '') ?? holding.asset?.name}
            </span>
            <input
              type="number"
              step="0.1"
              min="0"
              max="100"
              value={effective[holding.asset_id] ?? '0'}
              onChange={(e) => setWeights({ ...effective, [holding.asset_id]: e.target.value })}
              className="h-9 w-24 rounded border border-border bg-surface px-2 text-right text-sm tabular-nums text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            />
            <span className="w-4 text-sm text-text-muted">%</span>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <span className={`text-sm tabular-nums ${balanced ? 'text-text-secondary' : 'text-negative'}`}>
          Total: {totalPct.toFixed(1)}%{!balanced && ' — must add up to 100%'}
        </span>
        <Button size="sm" variant="secondary" onClick={setEqualWeight}>
          Equal weight
        </Button>
        <Button size="sm" variant="secondary" onClick={() => setWeights({})}>
          Reset to current
        </Button>
        <Button size="sm" onClick={run} disabled={!balanced || preview.isPending}>
          <Scale className="h-4 w-4" />
          {preview.isPending ? 'Simulating…' : 'Simulate'}
        </Button>
      </div>

      {preview.isError && (
        <p className="text-sm text-negative">
          {preview.error?.response?.data?.error?.message ?? 'Could not run the simulation.'}
        </p>
      )}

      {result && (
        <div className="space-y-3">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[30rem] text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase text-text-secondary">
                  <th className="py-2 pr-4">Metric</th>
                  <th className="py-2 pr-4 text-right">Current</th>
                  <th className="py-2 pr-4 text-right">Hypothetical</th>
                  <th className="py-2 text-right">Change</th>
                </tr>
              </thead>
              <tbody>
                <MetricRow
                  label="Volatility"
                  current={result.current.volatility}
                  hypothetical={result.hypothetical.volatility}
                  format={(v) => `${(v * 100).toFixed(2)}%`}
                />
                <MetricRow
                  label="Sharpe ratio"
                  current={result.current.sharpe}
                  hypothetical={result.hypothetical.sharpe}
                  format={(v) => v.toFixed(2)}
                />
                <MetricRow
                  label="Max drawdown"
                  current={result.current.max_drawdown}
                  hypothetical={result.hypothetical.max_drawdown}
                  format={(v) => `${(v * 100).toFixed(2)}%`}
                />
                <MetricRow
                  label="Beta"
                  current={result.current.beta}
                  hypothetical={result.hypothetical.beta}
                  format={(v) => v.toFixed(2)}
                />
                <MetricRow
                  label="Diversification"
                  current={result.current.diversification_score}
                  hypothetical={result.hypothetical.diversification_score}
                  format={(v) => v.toFixed(1)}
                />
                <MetricRow
                  label="Concentration (HHI)"
                  current={result.current.hhi}
                  hypothetical={result.hypothetical.hhi}
                  format={(v) => v.toFixed(3)}
                />
              </tbody>
            </table>
          </div>

          <div>
            <p className="mb-1.5 text-sm text-text-secondary">Implied shifts</p>
            <div className="space-y-1">
              {result.changes.map((change) => {
                const delta = Number(change.value_change)
                if (Math.abs(delta) < 1) return null
                return (
                  <div key={change.asset_id} className="flex items-center justify-between gap-3 text-sm">
                    <span className="min-w-0 truncate text-text-primary">
                      {change.symbol.replace(/\.(NS|BO)$/, '')}
                    </span>
                    <span className="shrink-0 tabular-nums text-text-secondary">
                      {Number(change.current_weight_pct).toFixed(1)}% →{' '}
                      {Number(change.target_weight_pct).toFixed(1)}%
                    </span>
                    <span
                      className={`w-28 shrink-0 text-right tabular-nums ${
                        delta >= 0 ? 'text-positive' : 'text-negative'
                      }`}
                    >
                      {delta >= 0 ? '+' : ''}
                      {formatCurrency(delta)}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          {result.excluded_from_simulation?.length > 0 && (
            <p className="text-xs text-warning">
              Excluded from the simulated metrics:{' '}
              {result.excluded_from_simulation
                .map((e) => `${e.symbol} (${e.reason})`)
                .join(', ')}
              . Remaining weights were rescaled.
            </p>
          )}

          <p className="text-xs text-text-muted">{result.note}</p>
        </div>
      )}
    </div>
  )
}
