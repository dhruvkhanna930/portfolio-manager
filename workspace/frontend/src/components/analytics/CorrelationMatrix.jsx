import { Skeleton } from '../ui'
import { useCorrelation } from '../../hooks/useAdvancedAnalytics'

// Diverging scale: red = moves together (less diversification benefit),
// green = moves oppositely. Null is rendered as a dash, never as 0 -- "we
// couldn't measure this" and "these are uncorrelated" are different claims.
function cellStyle(value) {
  if (value == null) return { className: 'text-text-muted', style: undefined }
  const intensity = Math.min(1, Math.abs(value))
  const alpha = 0.08 + intensity * 0.42
  const color = value >= 0 ? `rgba(239, 68, 68, ${alpha})` : `rgba(34, 197, 94, ${alpha})`
  return { className: 'text-text-primary', style: { backgroundColor: color } }
}

export default function CorrelationMatrix({ period = '1Y' }) {
  const { data, isLoading } = useCorrelation(period)

  if (isLoading) return <Skeleton className="h-64 w-full rounded" />
  if (!data?.assets?.length) {
    return <p className="text-sm text-text-secondary">Add at least two holdings to see correlations.</p>
  }

  const labels = data.assets.map((a) => a.symbol.replace(/\.(NS|BO)$/, ''))

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto">
        <table className="text-xs">
          <thead>
            <tr>
              <th className="sticky left-0 z-10 bg-surface p-2" />
              {labels.map((label) => (
                <th key={label} className="p-2 text-center font-medium text-text-secondary">
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.matrix.map((row, i) => (
              <tr key={data.assets[i].asset_id}>
                <th
                  className="sticky left-0 z-10 whitespace-nowrap bg-surface p-2 text-left font-medium text-text-secondary"
                  title={data.assets[i].name}
                >
                  {labels[i]}
                </th>
                {row.map((value, j) => {
                  const { className, style } = cellStyle(value)
                  return (
                    <td
                      key={`${data.assets[i].asset_id}-${data.assets[j].asset_id}`}
                      className={`p-2 text-center tabular-nums ${className}`}
                      style={style}
                      title={`${labels[i]} vs ${labels[j]}`}
                    >
                      {value == null ? '—' : value.toFixed(2)}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-text-muted">{data.note}</p>
    </div>
  )
}
