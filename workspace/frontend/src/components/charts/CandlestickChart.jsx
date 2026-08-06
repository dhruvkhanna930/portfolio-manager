import { useEffect, useRef } from 'react'
import { AreaSeries, CandlestickSeries, createChart } from 'lightweight-charts'
import Skeleton from '../ui/Skeleton'
import EmptyState from '../ui/EmptyState'
import { chartTokens } from './chartTheme'

function toTime(t) {
  // Cached daily rows arrive as plain 'YYYY-MM-DD' -- lightweight-charts takes
  // that directly as a business-day string. Intraday/2-point rows carry a full
  // ISO datetime and need converting to a UTC unix timestamp instead.
  if (/^\d{4}-\d{2}-\d{2}$/.test(t)) return t
  return Math.floor(new Date(t).getTime() / 1000)
}

function toSeriesData(points, hasOhlc) {
  const seen = new Set()
  const sorted = [...points]
    .map((p) => ({ ...p, time: toTime(p.t) }))
    .sort((a, b) => (a.time > b.time ? 1 : a.time < b.time ? -1 : 0))
    .filter((p) => {
      if (seen.has(p.time)) return false
      seen.add(p.time)
      return true
    })

  if (hasOhlc) {
    return sorted
      .filter((p) => p.open != null)
      .map((p) => ({
        time: p.time,
        open: Number(p.open),
        high: Number(p.high),
        low: Number(p.low),
        close: Number(p.close),
      }))
  }
  return sorted.map((p) => ({ time: p.time, value: Number(p.close) }))
}

export default function CandlestickChart({ points = [], loading = false, height = 340 }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  const hasOhlc = points.some((p) => p.open != null)
  const usesTimestamp = points.length > 0 && !/^\d{4}-\d{2}-\d{2}$/.test(points[0].t)
  const seriesData = toSeriesData(points, hasOhlc)

  useEffect(() => {
    if (!containerRef.current || seriesData.length === 0) return undefined

    // lightweight-charts is imperative and reads its colours once at creation,
    // so tokens are resolved here rather than at render.
    const t = chartTokens()

    const chart = createChart(containerRef.current, {
      height,
      layout: { background: { color: 'transparent' }, textColor: t.textSecondary },
      grid: {
        vertLines: { color: t.surfaceHover },
        horzLines: { color: t.surfaceHover },
      },
      rightPriceScale: { borderColor: t.border },
      timeScale: {
        borderColor: t.border,
        timeVisible: usesTimestamp,
        secondsVisible: false,
      },
      crosshair: { mode: 0 },
    })
    chartRef.current = chart

    const series = hasOhlc
      ? chart.addSeries(CandlestickSeries, {
          upColor: t.positive,
          downColor: t.negative,
          borderVisible: false,
          wickUpColor: t.positive,
          wickDownColor: t.negative,
        })
      : chart.addSeries(AreaSeries, {
          lineColor: t.accent,
          topColor: `color-mix(in srgb, ${t.accent} 28%, transparent)`,
          bottomColor: `color-mix(in srgb, ${t.accent} 0%, transparent)`,
          lineWidth: 2,
        })

    series.setData(seriesData)
    chart.timeScale().fitContent()

    const resizeObserver = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect?.width
      if (width) chart.applyOptions({ width })
    })
    resizeObserver.observe(containerRef.current)

    return () => {
      resizeObserver.disconnect()
      chart.remove()
      chartRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(seriesData), hasOhlc, usesTimestamp, height])

  if (loading) {
    return <Skeleton className="w-full rounded" style={{ height }} />
  }

  if (points.length === 0) {
    return (
      <div style={{ height }} className="flex items-center justify-center">
        <EmptyState title="No price data yet" description="This asset has no cached history for this period." />
      </div>
    )
  }

  return (
    <div>
      <div ref={containerRef} style={{ height }} className="w-full" />
      <p className="mt-2 text-right text-[11px] text-text-muted">
        Charts by{' '}
        <a
          href="https://www.tradingview.com/lightweight-charts/"
          target="_blank"
          rel="noreferrer"
          className="underline hover:text-text-secondary"
        >
          TradingView Lightweight Charts
        </a>
      </p>
    </div>
  )
}
