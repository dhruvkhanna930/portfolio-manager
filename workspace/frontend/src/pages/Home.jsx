import { Card } from '../components/ui'
import PortfolioHero from '../components/home/PortfolioHero'
import MoversCard from '../components/home/MoversCard'
import CondensedHoldingsTable from '../components/home/CondensedHoldingsTable'
import AllocationBar from '../components/charts/AllocationBar'
import NewsList from '../components/news/NewsList'
import { toHoldingRows } from '../components/portfolio/HoldingsTable'
import { useHoldings } from '../hooks/useHoldings'
import { useAllocation, usePortfolioSummary } from '../hooks/useAnalytics'
import { useMovers } from '../hooks/useMarket'
import { useGeneralNews } from '../hooks/useNews'

export default function Home() {
  const { data: holdings = [], isLoading: holdingsLoading } = useHoldings()
  const { data: summary, isLoading: summaryLoading } = usePortfolioSummary()
  const { data: sectorAllocation, isLoading: allocationLoading } = useAllocation('sector')
  const { data: portfolioMovers, isLoading: portfolioMoversLoading } = useMovers('portfolio', 5)
  const { data: indexMovers, isLoading: indexMoversLoading } = useMovers('index', 5)
  const { data: news = [], isLoading: newsLoading, error: newsError } = useGeneralNews(10)

  const rows = toHoldingRows(holdings)
  const totalCurrent = summary ? Number(summary.total_current) : 0
  const dayPl = summary ? Number(summary.day_pl) : 0
  const prevClose = totalCurrent - dayPl
  const dayPlPct = prevClose !== 0 ? (dayPl / prevClose) * 100 : 0
  const unrealisedPl = summary ? Number(summary.unrealised_pl) : 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">Home</h1>
        <p className="mt-1 text-text-secondary">Your portfolio at a glance, plus what the market's doing.</p>
      </div>

      <PortfolioHero
        totalValue={totalCurrent}
        dayPl={dayPl}
        dayPlPct={dayPlPct}
        totalPl={unrealisedPl}
        totalPlPct={summary ? Number(summary.total_pl_pct) : 0}
        loading={summaryLoading}
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <MoversCard
          title="Your Portfolio Movers"
          subtitle="Day-change across the assets you hold"
          gainers={portfolioMovers?.gainers}
          losers={portfolioMovers?.losers}
          loading={portfolioMoversLoading}
        />
        <MoversCard
          title="Market Movers"
          subtitle="Day-change across the Nifty 50 basket"
          gainers={indexMovers?.gainers}
          losers={indexMovers?.losers}
          loading={indexMoversLoading}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-text-secondary">
            Holdings
          </h2>
          <CondensedHoldingsTable rows={rows} loading={holdingsLoading} />
        </Card>

        <Card>
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-text-secondary">
            Allocation by Sector
          </h2>
          <AllocationBar items={sectorAllocation?.items ?? []} loading={allocationLoading} />
        </Card>
      </div>

      <div>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-text-secondary">
          Market News
        </h2>
        <NewsList news={news} loading={newsLoading} error={newsError} showAsset={false} />
      </div>
    </div>
  )
}
