import { useState } from 'react'
import { Plus, RefreshCw } from 'lucide-react'
import { Button, Card, KpiCard, Tabs, showToast } from '../components/ui'
import BuyModal from '../components/portfolio/BuyModal'
import SellModal from '../components/portfolio/SellModal'
import HoldingsTable, { toHoldingRows } from '../components/portfolio/HoldingsTable'
import WalletBalance from '../components/wallet/WalletBalance'
import AllocationDonut from '../components/charts/AllocationDonut'
import PerformanceChart from '../components/charts/PerformanceChart'
import { useHoldings } from '../hooks/useHoldings'
import { useSyncPrices } from '../hooks/usePrices'
import { useWallet } from '../hooks/useWallet'
import { useCreateSip, useCreateTransaction } from '../hooks/useTransactions'
import { useAllocation, usePortfolioSummary } from '../hooks/useAnalytics'
import { getApiErrorMessage } from '../utils/apiError'
import { formatCurrency } from '../utils/formatters'

const ALLOCATION_TABS = [
  { key: 'type', label: 'By Type' },
  { key: 'sector', label: 'By Sector' },
  { key: 'holding', label: 'By Holding' },
]

export default function Portfolio() {
  const { data: holdings = [], isLoading } = useHoldings()
  const { data: summary, isLoading: summaryLoading } = usePortfolioSummary()
  const { data: wallet } = useWallet()
  const [allocationBy, setAllocationBy] = useState('type')
  const { data: allocation, isLoading: allocationLoading } = useAllocation(allocationBy)
  const syncPrices = useSyncPrices()
  const createTransaction = useCreateTransaction()
  const createSip = useCreateSip()

  const [buyOpen, setBuyOpen] = useState(false)
  const [sellTarget, setSellTarget] = useState(null)
  const [sellAll, setSellAll] = useState(false)

  const walletBalance = wallet ? Number(wallet.balance) : 0

  const rows = toHoldingRows(holdings)

  const totalCurrent = summary ? Number(summary.total_current) : 0
  const dayPl = summary ? Number(summary.day_pl) : 0
  const prevClose = totalCurrent - dayPl
  const dayPlPct = prevClose !== 0 ? (dayPl / prevClose) * 100 : 0
  const realisedPl = summary ? Number(summary.realised_pl) : 0
  const unrealisedPl = summary ? Number(summary.unrealised_pl) : 0

  const openSell = (holding, all = false) => {
    setSellAll(all)
    setSellTarget(holding)
  }

  const handleBuy = (payload) => {
    createTransaction.mutate(payload, {
      onSuccess: () => {
        showToast.success('Buy recorded')
        setBuyOpen(false)
      },
      onError: (error) => showToast.error(getApiErrorMessage(error, 'Buy failed')),
    })
  }

  const handleSell = (payload) => {
    createTransaction.mutate(payload, {
      onSuccess: ({ realised_pl }) => {
        const realised = Number(realised_pl ?? 0)
        showToast.success(
          `Sell recorded · realised ${realised >= 0 ? '+' : ''}${formatCurrency(realised)}`
        )
        setSellTarget(null)
      },
      onError: (error) => showToast.error(getApiErrorMessage(error, 'Sell failed')),
    })
  }

  const handleCreateSip = (payload) => {
    createSip.mutate(payload, {
      onSuccess: () => {
        showToast.success('SIP plan created — no cash debited')
        setBuyOpen(false)
      },
      onError: (error) => showToast.error(getApiErrorMessage(error, 'Could not create SIP')),
    })
  }

  const handleSyncPrices = () => {
    syncPrices.mutate(undefined, {
      onSuccess: ({ summary: s }) => {
        if (s.updated === 0 && s.stale === 0 && s.failed === 0) {
          showToast.info('No live-priced assets to sync')
        } else if (s.updated > 0 && s.stale === 0 && s.failed === 0) {
          showToast.success(`Synced ${s.updated} price${s.updated === 1 ? '' : 's'}`)
        } else {
          showToast.info(
            `${s.updated} updated, ${s.stale} fell back to stale cache${
              s.failed > 0 ? `, ${s.failed} failed` : ''
            }`
          )
        }
      },
      onError: (error) => showToast.error(getApiErrorMessage(error, 'Price sync failed')),
    })
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">My Portfolio</h1>
          <p className="mt-1 text-text-secondary">Your stocks, mutual funds, and bonds.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <WalletBalance />
          <Button variant="secondary" onClick={handleSyncPrices} disabled={syncPrices.isPending}>
            <RefreshCw className={`h-4 w-4 ${syncPrices.isPending ? 'animate-spin' : ''}`} />
            Sync Prices
          </Button>
          <Button onClick={() => setBuyOpen(true)}>
            <Plus className="h-4 w-4" />
            Buy
          </Button>
        </div>
      </div>

      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Total Value" value={totalCurrent} format="currency" loading={summaryLoading} />
        <KpiCard
          label="Invested"
          value={summary ? Number(summary.total_invested) : 0}
          format="currency"
          loading={summaryLoading}
        />
        <div className="rounded border border-border bg-surface p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-text-secondary">
            Total P/L
          </p>
          <p
            className={`mt-2 text-2xl font-semibold tabular-nums ${
              unrealisedPl >= 0 ? 'text-positive' : 'text-negative'
            }`}
          >
            {unrealisedPl >= 0 ? '+' : ''}
            {formatCurrency(unrealisedPl)}
          </p>
          <div className="mt-2 space-y-0.5 text-xs">
            <p className="flex items-center justify-between gap-2">
              <span className="text-text-secondary">Unrealised</span>
              <span
                className={`tabular-nums ${unrealisedPl >= 0 ? 'text-positive' : 'text-negative'}`}
              >
                {unrealisedPl >= 0 ? '+' : ''}
                {formatCurrency(unrealisedPl)}
              </span>
            </p>
            <p className="flex items-center justify-between gap-2">
              <span className="text-text-secondary">Realised</span>
              <span className={`tabular-nums ${realisedPl >= 0 ? 'text-positive' : 'text-negative'}`}>
                {realisedPl >= 0 ? '+' : ''}
                {formatCurrency(realisedPl)}
              </span>
            </p>
          </div>
        </div>
        <KpiCard
          label="Today's P/L"
          value={dayPl}
          changePct={dayPlPct}
          format="currency"
          loading={summaryLoading}
        />
      </div>

      <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <PerformanceChart />
        </Card>

        <Card>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-sm font-medium uppercase tracking-wide text-text-secondary">
              Allocation
            </h2>
            <Tabs tabs={ALLOCATION_TABS} value={allocationBy} onChange={setAllocationBy} />
          </div>
          <AllocationDonut items={allocation?.items ?? []} loading={allocationLoading} />
        </Card>
      </div>

      <HoldingsTable
        rows={rows}
        loading={isLoading}
        onSell={(row) => openSell(row, false)}
        onSellAll={(row) => openSell(row, true)}
        emptyDescription="Deposit some cash, then buy your first stock or mutual fund."
        emptyAction={
          <Button size="sm" onClick={() => setBuyOpen(true)}>
            Buy an asset
          </Button>
        }
      />

      <BuyModal
        open={buyOpen}
        onClose={() => setBuyOpen(false)}
        walletBalance={walletBalance}
        onBuy={handleBuy}
        onCreateSip={handleCreateSip}
        submitting={createTransaction.isPending || createSip.isPending}
      />

      <SellModal
        open={Boolean(sellTarget)}
        onClose={() => setSellTarget(null)}
        holding={sellTarget}
        sellAll={sellAll}
        onSell={handleSell}
        submitting={createTransaction.isPending}
      />
    </div>
  )
}
