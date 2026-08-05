/**
 * Risk vs. return bubble scatter panel (§15.2).
 *
 * Holdings without enough price history are listed under the chart rather than
 * omitted silently — being unmeasurable is itself information about a position.
 */

import { AlertTriangle } from 'lucide-react'

import { Skeleton } from '../ui'
import RiskReturnScatter from '../charts/RiskReturnScatter'
import { useRiskReturn } from '../../hooks/useVisualAnalytics'

export default function RiskReturnPanel({ period = '1Y' }) {
  const { data, isLoading } = useRiskReturn(period)

  if (isLoading) return <Skeleton className="h-80 w-full rounded" />
  if (!data) return null

  return (
    <div className="space-y-3">
      <RiskReturnScatter points={data.points} />

      <p className="text-xs text-text-muted">{data.note}</p>

      {data.excluded?.length > 0 && (
        <p className="flex items-start gap-1.5 text-xs text-warning">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <span>
            Not plotted:{' '}
            {data.excluded
              .map((e) => `${e.symbol.replace(/\.(NS|BO)$/, '')} (${e.reason})`)
              .join(', ')}
            .
          </span>
        </p>
      )}
    </div>
  )
}
