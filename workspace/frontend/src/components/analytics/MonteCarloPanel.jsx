import { useState } from 'react'
import { Play } from 'lucide-react'

import { Button, Input, Select } from '../ui'
import { useMonteCarlo } from '../../hooks/useAdvancedAnalytics'
import { formatCurrency } from '../../utils/formatters'

const HORIZONS = [
  { value: '63', label: '3 months' },
  { value: '126', label: '6 months' },
  { value: '252', label: '1 year' },
  { value: '756', label: '3 years' },
  { value: '1260', label: '5 years' },
]

export default function MonteCarloPanel() {
  const [horizon, setHorizon] = useState('252')
  const [simulations, setSimulations] = useState('1000')
  const monteCarlo = useMonteCarlo()
  const result = monteCarlo.data

  const run = () =>
    monteCarlo.mutate({
      horizonDays: Number(horizon),
      nSimulations: Number(simulations),
      period: 'ALL',
    })

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3">
        <div className="w-40">
          <Select
            id="mc_horizon"
            label="Horizon"
            options={HORIZONS}
            value={horizon}
            onChange={(e) => setHorizon(e.target.value)}
          />
        </div>
        <div className="w-40">
          <Input
            id="mc_sims"
            label="Simulations"
            type="number"
            min="100"
            max="2000"
            step="100"
            value={simulations}
            onChange={(e) => setSimulations(e.target.value)}
          />
        </div>
        <Button onClick={run} disabled={monteCarlo.isPending}>
          <Play className="h-4 w-4" />
          {monteCarlo.isPending ? 'Simulating…' : 'Run simulation'}
        </Button>
      </div>

      {monteCarlo.isError && (
        <p className="text-sm text-negative">Could not run the simulation. Please try again.</p>
      )}

      {result?.insufficient_data && <p className="text-sm text-text-secondary">{result.reason}</p>}

      {result && !result.insufficient_data && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="rounded border border-border bg-bg p-3">
              <p className="text-xs text-text-secondary">Starting value</p>
              <p className="mt-1 tabular-nums text-sm text-text-primary">
                {formatCurrency(result.start_value)}
              </p>
            </div>
            <div className="rounded border border-border bg-bg p-3">
              <p className="text-xs text-text-secondary">Pessimistic (10th pct)</p>
              <p className="mt-1 tabular-nums text-sm text-negative">
                {formatCurrency(result.final.p10)}
              </p>
            </div>
            <div className="rounded border border-border bg-bg p-3">
              <p className="text-xs text-text-secondary">Median (50th pct)</p>
              <p className="mt-1 tabular-nums text-sm text-text-primary">
                {formatCurrency(result.final.p50)}
              </p>
            </div>
            <div className="rounded border border-border bg-bg p-3">
              <p className="text-xs text-text-secondary">Optimistic (90th pct)</p>
              <p className="mt-1 tabular-nums text-sm text-positive">
                {formatCurrency(result.final.p90)}
              </p>
            </div>
          </div>

          <p className="text-sm text-text-secondary">
            In {Number(result.probability_of_loss_pct).toFixed(1)}% of {result.n_simulations}{' '}
            simulations the portfolio ended below its current value.
          </p>

          <details className="rounded border border-border bg-bg p-3">
            <summary className="cursor-pointer text-sm text-text-secondary">
              Show projected range over time
            </summary>
            <div className="mt-3 max-h-64 overflow-y-auto">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-bg">
                  <tr className="border-b border-border text-left text-text-secondary">
                    <th className="py-1.5 pr-4">Day</th>
                    <th className="py-1.5 pr-4 text-right">10th pct</th>
                    <th className="py-1.5 pr-4 text-right">Median</th>
                    <th className="py-1.5 text-right">90th pct</th>
                  </tr>
                </thead>
                <tbody>
                  {result.bands
                    .filter((_, i) => i % Math.ceil(result.bands.length / 20) === 0)
                    .map((band) => (
                      <tr key={band.day} className="border-b border-border/40">
                        <td className="py-1.5 pr-4 text-text-secondary">{band.day}</td>
                        <td className="py-1.5 pr-4 text-right tabular-nums text-negative">
                          {formatCurrency(band.p10, { compact: true })}
                        </td>
                        <td className="py-1.5 pr-4 text-right tabular-nums text-text-primary">
                          {formatCurrency(band.p50, { compact: true })}
                        </td>
                        <td className="py-1.5 text-right tabular-nums text-positive">
                          {formatCurrency(band.p90, { compact: true })}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </details>

          <p className="text-xs text-text-muted">
            Method: {result.method}, from {result.observations} historical daily observations.{' '}
            {result.disclaimer}
          </p>
        </div>
      )}
    </div>
  )
}
