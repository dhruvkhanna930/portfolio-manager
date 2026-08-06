/**
 * Rebalancing simulator (§15.5 UI over §14.8's endpoint).
 *
 * Sliders drive a live recompute, debounced rather than fired per pixel: each
 * settled position is one POST that re-runs a full historical simulation
 * server-side. Firing on every pointer event would queue dozens of redundant
 * simulations and make the charts flicker between stale responses.
 *
 * Weights must total 100%. Rather than block on that, dragging one slider
 * proportionally absorbs the difference across the others, so the panel stays
 * in a valid state while the user explores. "Nothing is saved" is literal --
 * the endpoint persists nothing and no trade is placed.
 */

import { useEffect, useMemo, useRef, useState } from 'react'
import { RotateCcw, Scale } from 'lucide-react'

import { Button, Skeleton } from '../ui'
import PortfolioRadar from '../charts/PortfolioRadar'
import { useHoldings } from '../../hooks/useHoldings'
import { useRebalancePreview } from '../../hooks/useAdvancedAnalytics'
import { formatCurrency } from '../../utils/formatters'

const SIM_DEBOUNCE_MS = 320

function cleanSymbol(symbol) {
  return String(symbol ?? '').replace(/\.(NS|BO)$/, '')
}

function MetricRow({ label, current, hypothetical, format, lowerIsBetter = false }) {
  const fmt = (v) => (v == null ? '—' : format(v))
  const delta = current != null && hypothetical != null ? hypothetical - current : null
  const improved = delta == null ? null : lowerIsBetter ? delta < 0 : delta > 0
  return (
    <tr className="border-b border-border/50">
      <td className="py-2 pr-4 text-text-secondary">{label}</td>
      <td className="py-2 pr-4 text-right tabular-nums text-text-primary">{fmt(current)}</td>
      <td className="py-2 pr-4 text-right tabular-nums text-text-primary">{fmt(hypothetical)}</td>
      <td
        className={`py-2 text-right tabular-nums ${
          delta == null || delta === 0
            ? 'text-text-muted'
            : improved
              ? 'text-positive'
              : 'text-negative'
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
  const [weights, setWeights] = useState(null)
  const debounceRef = useRef()
  const runRef = useRef()

  const currentWeights = useMemo(() => {
    const total = holdings.reduce((sum, h) => sum + Number(h.current_value ?? 0), 0)
    if (!total) return {}
    return Object.fromEntries(
      holdings.map((h) => [h.asset_id, (Number(h.current_value ?? 0) / total) * 100])
    )
  }, [holdings])

  const effective = weights ?? currentWeights
  const total = Object.values(effective).reduce((sum, v) => sum + (Number(v) || 0), 0)

  // Keep the latest runner in a ref so the debounce effect doesn't need it as a
  // dependency (which would reset the timer on every render).
  runRef.current = () => {
    const target = Object.fromEntries(
      Object.entries(effective).map(([id, pct]) => [id, (Number(pct) || 0) / 100])
    )
    if (Object.keys(target).length) preview.mutate({ targetWeights: target, period })
  }

  useEffect(() => {
    if (!Object.keys(effective).length) return undefined
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => runRef.current?.(), SIM_DEBOUNCE_MS)
    return () => clearTimeout(debounceRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(effective), period])

  /** Move one holding to `next`, absorbing the change across the others pro rata. */
  const setWeight = (assetId, next) => {
    const base = { ...effective }
    const clamped = Math.max(0, Math.min(100, Number(next) || 0))
    const others = Object.keys(base).filter((id) => String(id) !== String(assetId))
    const othersTotal = others.reduce((sum, id) => sum + (Number(base[id]) || 0), 0)
    const remaining = 100 - clamped

    const updated = { [assetId]: clamped }
    if (othersTotal > 0) {
      others.forEach((id) => {
        updated[id] = (Number(base[id]) / othersTotal) * remaining
      })
    } else if (others.length) {
      // Everything else was at zero -- split the remainder evenly rather than
      // leaving the total short of 100.
      others.forEach((id) => {
        updated[id] = remaining / others.length
      })
    }
    setWeights(updated)
  }

  const setEqualWeight = () => {
    const each = 100 / holdings.length
    setWeights(Object.fromEntries(holdings.map((h) => [h.asset_id, each])))
  }

  if (isLoading) return <Skeleton className="h-96 w-full rounded" />
  if (!holdings.length) {
    return <p className="text-sm text-text-secondary">No holdings to rebalance.</p>
  }

  const result = preview.data

  // Holdings the simulation had to drop for lack of price history. Worth marking
  // on the slider itself: because their weight is removed and the rest
  // renormalized, dragging one of these cannot change the simulated metrics at
  // all, and a slider that visibly does nothing reads as a bug.
  const excludedIds = new Set(
    (result?.excluded_from_simulation ?? []).map((e) => String(e.asset_id))
  )

  const radarItems = holdings
    .map((h) => ({
      label: cleanSymbol(h.asset?.symbol),
      pct: Number(effective[h.asset_id] ?? 0),
      value: Number(h.current_value ?? 0),
    }))
    .filter((i) => i.pct > 0.05)

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,20rem)]">
        <div className="space-y-3">
          {holdings.map((holding) => {
            const value = Number(effective[holding.asset_id] ?? 0)
            const currentValue = Number(currentWeights[holding.asset_id] ?? 0)
            const shifted = Math.abs(value - currentValue) > 0.05
            const excluded = excludedIds.has(String(holding.asset_id))
            return (
              <div key={holding.asset_id}>
                <div className="flex items-baseline justify-between gap-3 text-sm">
                  <span className="min-w-0 truncate text-text-primary" title={holding.asset?.name}>
                    {cleanSymbol(holding.asset?.symbol) || holding.asset?.name}
                    {excluded && (
                      <span
                        className="ml-2 text-xs font-normal text-warning"
                        title="Not enough price history to simulate — changing this weight won't move the metrics below."
                      >
                        not simulated
                      </span>
                    )}
                  </span>
                  <span className="shrink-0 tabular-nums">
                    <span className={shifted ? 'text-accent' : 'text-text-secondary'}>
                      {value.toFixed(1)}%
                    </span>
                    {shifted && (
                      <span className="ml-2 text-xs text-text-muted">
                        was {currentValue.toFixed(1)}%
                      </span>
                    )}
                  </span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={100}
                  step={0.5}
                  value={value}
                  onChange={(e) => setWeight(holding.asset_id, e.target.value)}
                  aria-label={`Target weight for ${cleanSymbol(holding.asset?.symbol)}`}
                  className={`mt-1.5 h-1.5 w-full cursor-pointer appearance-none rounded-full bg-surface-hover ${
                    excluded ? 'accent-warning opacity-60' : 'accent-accent'
                  }`}
                />
              </div>
            )
          })}

          <div className="flex flex-wrap items-center gap-3 pt-1">
            <span className="text-sm tabular-nums text-text-secondary">
              Total: {total.toFixed(1)}%
            </span>
            <Button size="sm" variant="secondary" onClick={setEqualWeight}>
              <Scale className="h-4 w-4" />
              Equal weight
            </Button>
            <Button size="sm" variant="secondary" onClick={() => setWeights(null)}>
              <RotateCcw className="h-4 w-4" />
              Reset
            </Button>
            {preview.isPending && <span className="text-xs text-text-muted">Simulating…</span>}
          </div>
        </div>

        <div className="self-start">
          <p className="mb-1 text-xs text-text-secondary">Target mix</p>
          <PortfolioRadar items={radarItems} height={260} />
        </div>
      </div>

      {preview.isError && (
        <p className="text-sm text-negative">
          {preview.error?.response?.data?.error?.message ?? 'Could not run the simulation.'}
        </p>
      )}

      {result && (
        <div
          className={`space-y-3 transition-opacity ${preview.isPending ? 'opacity-60' : 'opacity-100'}`}
        >
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
                  lowerIsBetter
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
                  lowerIsBetter
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
                  lowerIsBetter
                />
              </tbody>
            </table>
          </div>

          <div>
            <p className="mb-1.5 text-sm text-text-secondary">Implied shifts</p>
            <div className="space-y-1">
              {result.changes
                .filter((c) => Math.abs(Number(c.value_change)) >= 1)
                .map((change) => {
                  const delta = Number(change.value_change)
                  return (
                    <div
                      key={change.asset_id}
                      className="flex items-center justify-between gap-3 text-sm"
                    >
                      <span className="min-w-0 truncate text-text-primary">
                        {cleanSymbol(change.symbol)}
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
              {result.excluded_from_simulation.map((e) => `${e.symbol} (${e.reason})`).join(', ')}.
              Remaining weights were rescaled.
            </p>
          )}

          <p className="text-xs text-text-muted">{result.note}</p>
        </div>
      )}
    </div>
  )
}
