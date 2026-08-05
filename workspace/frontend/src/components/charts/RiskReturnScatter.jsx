/**
 * Risk vs. return bubble scatter (§15.2).
 *
 * x = annualized volatility, y = annualized return, bubble area = position size.
 * Size is deliberately *area*-encoded via Recharts' ZAxis (which scales area,
 * not radius) -- radius-encoding exaggerates large positions roughly
 * quadratically, which is the classic bubble-chart lie.
 *
 * A quadrant guide at y=0 separates "made money" from "lost money" over the
 * window; there is no attempt to draw an efficient frontier (§0.3 item 20 rules
 * that out as easy to get subtly wrong).
 */

import {
  CartesianGrid,
  Cell,
  LabelList,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from 'recharts'

import { EmptyState } from '../ui'
import { axisProps, chartTokens, tooltipStyle } from './chartTheme'
import { formatCurrency } from '../../utils/formatters'

function cleanSymbol(symbol) {
  return String(symbol ?? '').replace(/\.(NS|BO)$/, '')
}

export default function RiskReturnScatter({ points = [], height = 340 }) {
  const usable = points.filter((p) => p.volatility != null && p.annualized_return != null)
  if (!usable.length) {
    return (
      <EmptyState
        title="Not enough price history"
        description="Risk and return need at least 30 daily observations per holding."
      />
    )
  }

  const t = chartTokens()
  const data = usable.map((p) => ({
    symbol: cleanSymbol(p.symbol),
    name: p.name,
    vol: p.volatility * 100,
    ret: p.annualized_return * 100,
    value: Number(p.current_value ?? 0),
    weight: p.weight_pct == null ? null : Number(p.weight_pct),
  }))

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 12, right: 18, bottom: 34, left: 8 }}>
          <CartesianGrid stroke={t.border} strokeDasharray="3 3" />
          <XAxis
            type="number"
            dataKey="vol"
            name="Volatility"
            unit="%"
            {...axisProps()}
            label={{
              value: 'Annualized volatility →',
              position: 'insideBottom',
              offset: -20,
              fill: t.textMuted,
              fontSize: 11,
            }}
          />
          <YAxis
            type="number"
            dataKey="ret"
            name="Return"
            unit="%"
            {...axisProps()}
            label={{
              value: 'Return →',
              angle: -90,
              position: 'insideLeft',
              fill: t.textMuted,
              fontSize: 11,
            }}
          />
          <ZAxis type="number" dataKey="value" range={[80, 900]} name="Position size" />
          <ReferenceLine y={0} stroke={t.textMuted} strokeDasharray="4 4" />
          <Tooltip
            {...tooltipStyle()}
            cursor={{ strokeDasharray: '3 3', stroke: t.border }}
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null
              const d = payload[0].payload
              return (
                <div className="rounded border border-border bg-surface p-2.5 text-xs shadow-lg">
                  <p className="font-medium text-text-primary">{d.symbol}</p>
                  <p className="mt-1 text-text-secondary">{d.name}</p>
                  <p className="mt-1.5 tabular-nums text-text-primary">
                    Volatility {d.vol.toFixed(1)}%
                  </p>
                  <p className="tabular-nums text-text-primary">Return {d.ret.toFixed(1)}%</p>
                  <p className="tabular-nums text-text-secondary">
                    {formatCurrency(d.value)}
                    {d.weight != null && ` · ${d.weight.toFixed(1)}% of portfolio`}
                  </p>
                </div>
              )
            }}
          />
          <Scatter data={data} isAnimationActive>
            <LabelList
              dataKey="symbol"
              position="top"
              offset={10}
              style={{ fill: t.textSecondary, fontSize: 10 }}
            />
            {data.map((d) => (
              <Cell
                key={d.symbol}
                fill={d.ret >= 0 ? t.positive : t.negative}
                fillOpacity={0.55}
                stroke={d.ret >= 0 ? t.positive : t.negative}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  )
}
