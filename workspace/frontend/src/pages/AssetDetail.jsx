import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Bookmark, BookmarkCheck, Landmark, LineChart, PiggyBank } from 'lucide-react'
import { Badge, Button, Card, Skeleton, Tabs, showToast } from '../components/ui'
import CandlestickChart from '../components/charts/CandlestickChart'
import NewsList from '../components/news/NewsList'
import { useAssetDetail, useSimilarAssets } from '../hooks/useAssets'
import { useAssetNews } from '../hooks/useNews'
import { usePriceHistory } from '../hooks/usePrices'
import { useToggleWatchlist } from '../hooks/useWatchlist'
import { formatCurrency, formatDate } from '../utils/formatters'
import { getApiErrorMessage } from '../utils/apiError'

const TYPE_ICON = { STOCK: LineChart, MUTUAL_FUND: PiggyBank, BOND: Landmark }

const PERIOD_TABS = [
  { key: '1D', label: '1D' },
  { key: '1W', label: '1W' },
  { key: '1M', label: '1M' },
  { key: '6M', label: '6M' },
  { key: '1Y', label: '1Y' },
  { key: '3Y', label: '3Y' },
  { key: '5Y', label: '5Y' },
  { key: 'ALL', label: 'ALL' },
]

function StatRow({ label, value }) {
  if (value == null || value === '') return null
  return (
    <div className="flex items-center justify-between gap-3 py-1.5 text-sm">
      <span className="text-text-secondary">{label}</span>
      <span className="text-right tabular-nums text-text-primary">{value}</span>
    </div>
  )
}

export default function AssetDetail() {
  const { assetId } = useParams()
  const [period, setPeriod] = useState('1M')
  const { data: asset, isLoading } = useAssetDetail(assetId)
  const { data: history, isLoading: historyLoading } = usePriceHistory(assetId, period)
  const { data: similar = [] } = useSimilarAssets(assetId)
  const { data: news = [], isLoading: newsLoading, error: newsError } = useAssetNews(assetId, 10)
  const watchlist = useToggleWatchlist(assetId)

  if (isLoading || !asset) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-80 w-full" />
      </div>
    )
  }

  const Icon = TYPE_ICON[asset.asset_type] ?? LineChart
  const price = asset.current_price != null ? Number(asset.current_price) : null
  const dayChange = asset.day_change != null ? Number(asset.day_change) : null
  const dayChangePct = asset.day_change_pct != null ? Number(asset.day_change_pct) : null
  const isUp = dayChange == null || dayChange >= 0

  const handleWatchlistToggle = () => {
    const mutation = asset.is_watchlisted ? watchlist.remove : watchlist.add
    mutation.mutate(undefined, {
      onSuccess: () =>
        showToast.success(asset.is_watchlisted ? 'Removed from watchlist' : 'Added to watchlist'),
      onError: (error) => showToast.error(getApiErrorMessage(error, 'Could not update watchlist')),
    })
  }

  // No intraday feed exists for mutual funds or bonds -- 1D is a labeled
  // 2-point "prev close vs latest" comparison, not a real curve (§4.2).
  const isTwoPointFallback =
    period === '1D' && asset.asset_type !== 'STOCK' && (history?.points?.length ?? 0) <= 2

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-surface-hover">
            <Icon className="h-6 w-6 text-accent" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-semibold text-text-primary">{asset.name}</h1>
              <Badge tone="neutral">{asset.asset_type.replace('_', ' ')}</Badge>
            </div>
            <p className="text-sm text-text-secondary">
              {asset.symbol}
              {asset.exchange ? ` · ${asset.exchange}` : ''}
            </p>
          </div>
        </div>
        <Button
          variant="secondary"
          onClick={handleWatchlistToggle}
          disabled={watchlist.add.isPending || watchlist.remove.isPending}
        >
          {asset.is_watchlisted ? (
            <>
              <BookmarkCheck className="h-4 w-4 text-accent" />
              Watchlisted
            </>
          ) : (
            <>
              <Bookmark className="h-4 w-4" />
              Add to Watchlist
            </>
          )}
        </Button>
      </div>

      <div>
        {price != null ? (
          <div className="flex items-baseline gap-3">
            <span className="text-3xl font-semibold tabular-nums text-text-primary">
              {formatCurrency(price)}
            </span>
            {dayChange != null && (
              <span className={`text-sm tabular-nums ${isUp ? 'text-positive' : 'text-negative'}`}>
                {dayChange >= 0 ? '+' : ''}
                {formatCurrency(dayChange)} ({dayChangePct >= 0 ? '+' : ''}
                {dayChangePct?.toFixed(2)}%)
              </span>
            )}
            {asset.is_stale && <Badge tone="warning">Stale price</Badge>}
          </div>
        ) : (
          <p className="text-text-secondary">
            No price yet
            {asset.asset_type === 'BOND' ? ' -- bonds are priced manually.' : '.'}
          </p>
        )}
        {asset.as_of && (
          <p className="mt-1 text-xs text-text-muted">As of {formatDate(asset.as_of)}</p>
        )}
      </div>

      <Card>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-sm font-medium uppercase tracking-wide text-text-secondary">
            Price Chart
          </h2>
          <Tabs tabs={PERIOD_TABS} value={period} onChange={setPeriod} />
        </div>
        {isTwoPointFallback && (
          <p className="mb-3 text-xs text-text-muted">
            {asset.asset_type === 'MUTUAL_FUND'
              ? "Mutual funds don't trade intraday -- showing latest NAV vs. previous close instead of a curve."
              : 'No live feed exists for bonds -- showing the latest manually-entered price vs. the previous one.'}
          </p>
        )}
        <CandlestickChart points={history?.points ?? []} loading={historyLoading} />
      </Card>

      <Card>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-text-secondary">
          Fundamentals
        </h2>
        <div className="grid grid-cols-1 gap-x-8 sm:grid-cols-2">
          {asset.asset_type === 'STOCK' && (
            <>
              <div>
                <StatRow label="Exchange" value={asset.exchange} />
                <StatRow label="Sector" value={asset.sector} />
                <StatRow label="Industry" value={asset.industry} />
                <StatRow label="Country" value={asset.country} />
              </div>
              <div>
                <StatRow
                  label="Market Cap"
                  value={asset.market_cap ? formatCurrency(asset.market_cap, { compact: true }) : null}
                />
                <StatRow label="P/E Ratio" value={asset.pe_ratio ? asset.pe_ratio.toFixed(2) : null} />
                <StatRow
                  label="52W High"
                  value={asset.week52_high ? formatCurrency(asset.week52_high) : null}
                />
                <StatRow
                  label="52W Low"
                  value={asset.week52_low ? formatCurrency(asset.week52_low) : null}
                />
              </div>
            </>
          )}

          {asset.asset_type === 'MUTUAL_FUND' && (
            <>
              <div>
                <StatRow label="Fund House" value={asset.fund_house} />
                <StatRow label="Category" value={asset.category} />
                <StatRow label="Sub-category" value={asset.sub_category} />
                <StatRow label="Plan" value={asset.plan_type} />
                <StatRow label="Option" value={asset.option_type} />
              </div>
              <div>
                <StatRow
                  label="Expense Ratio"
                  value={asset.expense_ratio ? `${Number(asset.expense_ratio).toFixed(2)}%` : null}
                />
                <StatRow
                  label="AUM"
                  value={asset.aum ? formatCurrency(asset.aum, { compact: true }) : null}
                />
                <StatRow label="Risk Level" value={asset.risk_level} />
                <StatRow label="Benchmark" value={asset.benchmark} />
              </div>
            </>
          )}

          {asset.asset_type === 'BOND' && (
            <>
              <div>
                <StatRow label="Issuer" value={asset.issuer} />
                <StatRow
                  label="Coupon Rate"
                  value={asset.coupon_rate ? `${Number(asset.coupon_rate).toFixed(2)}%` : null}
                />
                <StatRow
                  label="Face Value"
                  value={asset.face_value ? formatCurrency(asset.face_value) : null}
                />
              </div>
              <div>
                <StatRow label="Maturity Date" value={asset.maturity_date ? formatDate(asset.maturity_date) : null} />
                <StatRow label="Credit Rating" value={asset.credit_rating} />
                <StatRow label="Payment Frequency" value={asset.payment_frequency} />
                <StatRow
                  label="Current Yield"
                  value={asset.current_yield ? `${Number(asset.current_yield).toFixed(2)}%` : null}
                />
              </div>
            </>
          )}
        </div>

        {asset.description && (
          <p className="mt-4 border-t border-border pt-4 text-sm leading-relaxed text-text-secondary">
            {asset.description}
          </p>
        )}
      </Card>

      <div>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-text-secondary">
          News
        </h2>
        <NewsList
          news={news}
          loading={newsLoading}
          error={newsError}
          title={`${asset.name} News`}
          showAsset={false}
        />
      </div>

      {similar.length > 0 && (
        <div>
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-text-secondary">
            Similar Assets
          </h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {similar.map((s) => (
              <Link key={s.asset_id} to={`/asset/${s.asset_id}`}>
                <Card hover className="h-full">
                  <p className="truncate text-sm font-medium text-text-primary">{s.name}</p>
                  <p className="mt-1 text-xs text-text-muted">{s.symbol}</p>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
