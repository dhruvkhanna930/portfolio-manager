import { Line, LineChart, ResponsiveContainer } from 'recharts'
import { usePriceHistory } from '../../hooks/usePrices'
import Skeleton from '../ui/Skeleton'
import { chartTokens } from './chartTheme'

// A condensed, axis-free trend line for a single asset -- reuses the same
// price_history cache the Asset Detail candlestick chart reads from (§4.2),
// just rendered small enough to sit inline in a table row.
export default function Sparkline({ assetId, width = 96, height = 32 }) {
  const { data, isLoading } = usePriceHistory(assetId, '1M')

  if (isLoading) {
    return <Skeleton style={{ width, height }} className="rounded" />
  }

  if (!data?.points?.length) {
    return <div style={{ width, height }} />
  }

  const points = data.points.map((p) => ({ value: Number(p.close) }))
  if (points.length < 2) {
    return <div style={{ width, height }} />
  }

  const first = points[0].value
  const last = points[points.length - 1].value
  const t = chartTokens()
  const color = last >= first ? t.positive : t.negative

  return (
    <div style={{ width, height }}>
      <ResponsiveContainer>
        <LineChart data={points}>
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
