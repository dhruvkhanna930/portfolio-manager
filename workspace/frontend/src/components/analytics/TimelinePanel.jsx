/**
 * Portfolio timeline + replay (§15 item 3).
 *
 * The slider scrubs from the first transaction to today; the KPIs and donut
 * beside it show the portfolio's real state on the selected date, replayed from
 * the transaction log and cached prices by /api/portfolio/snapshot.
 *
 * Two deliberate choices:
 *   - The slider is debounced (not per-pixel): each distinct date is one HTTP
 *     read, and React Query keeps visited dates warm, so a second pass over the
 *     same range is instant.
 *   - Values are NOT animated per-tick while dragging. A count-up on every
 *     frame would still be mid-animation when the next date arrives, so the
 *     number on screen would lag the date under the user's finger.
 */

import { useEffect, useMemo, useRef, useState } from 'react'
import { Pause, Play, RotateCcw } from 'lucide-react'

import { Button, Skeleton } from '../ui'
import AllocationDonut from '../charts/AllocationDonut'
import CalendarHeatmap from '../charts/CalendarHeatmap'
import { usePortfolioSnapshot, useTimelineBounds } from '../../hooks/useVisualAnalytics'
import { useTransactions } from '../../hooks/useTransactions'
import { formatCurrency, formatDate, formatPercent } from '../../utils/formatters'

const SCRUB_DEBOUNCE_MS = 90
const PLAYBACK_STEP_MS = 260
const PLAYBACK_STEPS = 40

function toIso(d) {
  return d.toISOString().slice(0, 10)
}

function dayCount(startIso, endIso) {
  return Math.max(0, Math.round((Date.parse(endIso) - Date.parse(startIso)) / 86_400_000))
}

function addDays(startIso, days) {
  return toIso(new Date(Date.parse(startIso) + days * 86_400_000))
}

export default function TimelinePanel() {
  const { data: bounds, isLoading: boundsLoading } = useTimelineBounds()
  const { data: transactions = [] } = useTransactions()

  const [offset, setOffset] = useState(null)
  const [committed, setCommitted] = useState(null)
  const [playing, setPlaying] = useState(false)
  const debounceRef = useRef()

  const totalDays = bounds?.has_data ? dayCount(bounds.start_date, bounds.end_date) : 0

  // Land on "today" once bounds arrive, so the panel opens showing the present.
  useEffect(() => {
    if (bounds?.has_data && offset === null) {
      setOffset(totalDays)
      setCommitted(totalDays)
    }
  }, [bounds, totalDays, offset])

  // Debounce scrubbing into one fetch per settled position.
  useEffect(() => {
    if (offset === null) return undefined
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => setCommitted(offset), SCRUB_DEBOUNCE_MS)
    return () => clearTimeout(debounceRef.current)
  }, [offset])

  useEffect(() => {
    if (!playing || offset === null) return undefined
    if (offset >= totalDays) {
      setPlaying(false)
      return undefined
    }
    const step = Math.max(1, Math.ceil(totalDays / PLAYBACK_STEPS))
    const timer = setTimeout(() => setOffset((o) => Math.min(totalDays, o + step)), PLAYBACK_STEP_MS)
    return () => clearTimeout(timer)
  }, [playing, offset, totalDays])

  const selectedDate = bounds?.has_data && offset !== null ? addDays(bounds.start_date, offset) : null
  const committedDate =
    bounds?.has_data && committed !== null ? addDays(bounds.start_date, committed) : null

  const { data: snapshot, isFetching } = usePortfolioSnapshot(committedDate)

  const events = useMemo(
    () =>
      transactions.map((t) => ({
        date: t.txn_date,
        type: t.txn_type,
        symbol: t.asset?.symbol,
      })),
    [transactions]
  )

  if (boundsLoading) return <Skeleton className="h-72 w-full rounded" />
  if (!bounds?.has_data) {
    return (
      <p className="text-sm text-text-secondary">
        No transactions yet — buy something and your history will appear here.
      </p>
    )
  }

  const atToday = offset === totalDays
  const pl = snapshot ? Number(snapshot.total_pl) : 0

  return (
    <div className="space-y-5">
      <div>
        <p className="mb-2 text-sm font-medium text-text-primary">Activity</p>
        <CalendarHeatmap
          events={events}
          months={12}
          onSelectDate={(iso) => {
            const next = dayCount(bounds.start_date, iso)
            if (next >= 0 && next <= totalDays) {
              setPlaying(false)
              setOffset(next)
            }
          }}
        />
      </div>

      <div className="border-t border-border pt-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-medium text-text-primary">Replay</p>
            <p className="text-xs text-text-secondary">
              Drag to see what you actually held on any date.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => setPlaying((p) => !p)}
              disabled={atToday && !playing}
            >
              {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              {playing ? 'Pause' : 'Play'}
            </Button>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => {
                setPlaying(false)
                setOffset(0)
              }}
            >
              <RotateCcw className="h-4 w-4" />
              Start
            </Button>
          </div>
        </div>

        <div className="mt-4">
          <input
            type="range"
            min={0}
            max={totalDays}
            value={offset ?? 0}
            onChange={(e) => {
              setPlaying(false)
              setOffset(Number(e.target.value))
            }}
            aria-label="Scrub portfolio history"
            className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-surface-hover accent-accent"
          />
          <div className="mt-2 flex items-center justify-between text-xs text-text-muted">
            <span>{formatDate(bounds.start_date)}</span>
            <span className="tabular-nums text-sm font-medium text-text-primary">
              {selectedDate && formatDate(selectedDate)}
              {atToday && <span className="ml-1.5 text-xs text-text-muted">(today)</span>}
            </span>
            <span>{formatDate(bounds.end_date)}</span>
          </div>
        </div>
      </div>

      <div
        className={`grid grid-cols-1 gap-4 transition-opacity lg:grid-cols-[minmax(0,1fr)_minmax(0,27rem)] ${
          isFetching ? 'opacity-70' : 'opacity-100'
        }`}
      >
        <div className="grid grid-cols-2 gap-3 self-start">
          <div className="rounded border border-border bg-bg p-3">
            <p className="text-xs text-text-secondary">Value on this date</p>
            <p className="mt-1 text-lg font-semibold tabular-nums text-text-primary">
              {snapshot ? formatCurrency(snapshot.total_current) : '—'}
            </p>
          </div>
          <div className="rounded border border-border bg-bg p-3">
            <p className="text-xs text-text-secondary">Invested</p>
            <p className="mt-1 text-lg font-semibold tabular-nums text-text-primary">
              {snapshot ? formatCurrency(snapshot.total_invested) : '—'}
            </p>
          </div>
          <div className="rounded border border-border bg-bg p-3">
            <p className="text-xs text-text-secondary">Unrealised P/L</p>
            <p
              className={`mt-1 text-lg font-semibold tabular-nums ${
                pl >= 0 ? 'text-positive' : 'text-negative'
              }`}
            >
              {snapshot ? formatCurrency(pl) : '—'}
            </p>
            {snapshot?.total_pl_pct != null && (
              <p className={`text-xs tabular-nums ${pl >= 0 ? 'text-positive' : 'text-negative'}`}>
                {formatPercent(Number(snapshot.total_pl_pct))}
              </p>
            )}
          </div>
          <div className="rounded border border-border bg-bg p-3">
            <p className="text-xs text-text-secondary">Holdings</p>
            <p className="mt-1 text-lg font-semibold tabular-nums text-text-primary">
              {snapshot ? snapshot.holdings_count : '—'}
            </p>
          </div>
        </div>

        <div>
          <p className="mb-1 text-xs text-text-secondary">Allocation by sector on this date</p>
          <AllocationDonut items={snapshot?.sectors ?? []} />
        </div>
      </div>

      {snapshot?.unpriced?.length > 0 && (
        <p className="text-xs text-warning">
          No cached price on this date for:{' '}
          {snapshot.unpriced.map((u) => u.symbol.replace(/\.(NS|BO)$/, '')).join(', ')}. Those
          positions are excluded from the totals above rather than counted as zero.
        </p>
      )}

      <p className="text-xs text-text-muted">
        Replayed from your transaction log and cached daily closes. Cost basis is recomputed as of
        the selected date, so it reflects only the purchases you had made by then.
      </p>
    </div>
  )
}
