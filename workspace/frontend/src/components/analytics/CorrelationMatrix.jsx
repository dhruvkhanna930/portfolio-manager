/**
 * Correlation panel — thin wrapper that fetches §14.2 and hands it to the
 * §15.2 heatmap. The colour scale, null handling and legend live in the chart
 * component so the same rendering can be reused elsewhere (e.g. the report).
 */

import { Skeleton } from '../ui'
import CorrelationHeatmap from '../charts/CorrelationHeatmap'
import { useCorrelation } from '../../hooks/useAdvancedAnalytics'

export default function CorrelationMatrix({ period = '1Y' }) {
  const { data, isLoading } = useCorrelation(period)

  if (isLoading) return <Skeleton className="h-64 w-full rounded" />
  if (!data?.assets?.length) {
    return (
      <p className="text-sm text-text-secondary">
        Add at least two holdings to see correlations.
      </p>
    )
  }

  return (
    <div className="space-y-3">
      <CorrelationHeatmap assets={data.assets} matrix={data.matrix} />
      <p className="text-xs text-text-muted">{data.note}</p>
    </div>
  )
}
