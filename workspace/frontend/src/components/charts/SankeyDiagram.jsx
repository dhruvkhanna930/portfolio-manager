/**
 * Cash-flow Sankey (§15.2): deposits → wallet → buys/sells/fees.
 *
 * Built on d3-sankey because Recharts has no native Sankey. Flows are absolute
 * rupee amounts from wallet_ledger, so link thickness is directly comparable
 * across the diagram.
 *
 * Withdrawals and cash still sitting in the wallet are shown as their own
 * terminal nodes rather than being dropped -- otherwise inflow and outflow
 * wouldn't balance and the diagram would quietly misstate where money went.
 */

import { useMemo, useState } from 'react'
import { sankey, sankeyLinkHorizontal, sankeyJustify } from 'd3-sankey'

import { EmptyState } from '../ui'
import { chartTokens, seriesColor } from './chartTheme'
import { formatCurrency } from '../../utils/formatters'

const NODE_WIDTH = 12
const NODE_PADDING = 14

export default function SankeyDiagram({ nodes = [], links = [], height = 340 }) {
  const [hover, setHover] = useState(null)
  const [width, setWidth] = useState(720)
  const t = chartTokens()

  const graph = useMemo(() => {
    if (!nodes.length || !links.length) return null
    const layout = sankey()
      .nodeId((d) => d.id)
      .nodeWidth(NODE_WIDTH)
      .nodePadding(NODE_PADDING)
      .nodeAlign(sankeyJustify)
      .extent([[1, 8], [width - 1, height - 8]])
    try {
      // d3-sankey mutates its input, so hand it copies.
      return layout({
        nodes: nodes.map((n) => ({ ...n })),
        links: links.map((l) => ({ ...l })),
      })
    } catch {
      // A cycle or an orphaned node id would throw; a missing diagram is a
      // better outcome than a crashed page.
      return null
    }
  }, [nodes, links, width, height])

  if (!graph) {
    return (
      <EmptyState
        title="No cash flow to trace"
        description="Deposit cash and make a transaction to see the flow."
      />
    )
  }

  const path = sankeyLinkHorizontal()

  return (
    <div className="space-y-2">
      <div
        className="w-full overflow-x-auto"
        ref={(el) => {
          if (el && el.clientWidth && Math.abs(el.clientWidth - width) > 8) setWidth(el.clientWidth)
        }}
      >
        <svg width={width} height={height} role="img" aria-label="Cash flow diagram">
          <g fill="none">
            {graph.links.map((link, i) => {
              const active = hover === null || hover === link.source.id || hover === link.target.id
              return (
                <path
                  key={i}
                  d={path(link)}
                  stroke={link.color ?? t.accent}
                  strokeOpacity={active ? 0.34 : 0.08}
                  strokeWidth={Math.max(1, link.width)}
                  onMouseEnter={() => setHover(link.source.id)}
                  onMouseLeave={() => setHover(null)}
                >
                  <title>
                    {link.source.label} → {link.target.label}: {formatCurrency(link.value)}
                  </title>
                </path>
              )
            })}
          </g>
          <g>
            {graph.nodes.map((node, i) => {
              const active = hover === null || hover === node.id
              const nodeHeight = Math.max(2, node.y1 - node.y0)
              const labelLeft = node.x0 > width / 2
              return (
                <g
                  key={node.id}
                  onMouseEnter={() => setHover(node.id)}
                  onMouseLeave={() => setHover(null)}
                  opacity={active ? 1 : 0.35}
                >
                  <rect
                    x={node.x0}
                    y={node.y0}
                    width={node.x1 - node.x0}
                    height={nodeHeight}
                    rx={2}
                    fill={node.color ?? seriesColor(i)}
                  >
                    <title>
                      {node.label}: {formatCurrency(node.value)}
                    </title>
                  </rect>
                  {nodeHeight > 9 && (
                    <text
                      x={labelLeft ? node.x0 - 6 : node.x1 + 6}
                      y={(node.y0 + node.y1) / 2}
                      textAnchor={labelLeft ? 'end' : 'start'}
                      dominantBaseline="middle"
                      fill={t.textSecondary}
                      style={{ fontSize: 10 }}
                    >
                      {node.label}
                      <tspan fill={t.textMuted}>
                        {' '}
                        {formatCurrency(node.value, { compact: true })}
                      </tspan>
                    </text>
                  )}
                </g>
              )
            })}
          </g>
        </svg>
      </div>
      <p className="text-xs text-text-muted">
        Every rupee that entered your wallet, and where it went. Widths are absolute amounts from
        your ledger.
      </p>
    </div>
  )
}
