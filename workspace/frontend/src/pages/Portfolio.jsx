import { useState } from 'react'
import { Plus, RefreshCw } from 'lucide-react'
import { Button, Card, DataTable, EmptyState, KpiCard, Modal, Tabs, showToast } from '../components/ui'
import BuyModal from '../components/portfolio/BuyModal'
import SellModal from '../components/portfolio/SellModal'
import WalletBalance from '../components/wallet/WalletBalance'
import AllocationDonut from '../components/charts/AllocationDonut'
import { useHoldings } from '../hooks/useHoldings'
import { useSyncPrices } from '../hooks/usePrices'
import { useWallet } from '../hooks/useWallet'
import { useCreateSip, useCreateTransaction } from '../hooks/useTransactions'
import { useAllocation, usePortfolioSummary } from '../hooks/useAnalytics'
import { getApiErrorMessage } from '../utils/apiError'
import { formatCurrency, formatNumber, formatPercent } from '../utils/formatters'

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

  const rows = holdings.map((h) => ({
    ...h,
    name: h.asset.name,
    type: h.asset.asset_type.replace('_', ' '),
    quantity: Number(h.quantity),
    avg_buy_price: Number(h.avg_buy_price),
    current_value: Number(h.current_value),
    weight_pct: Number(h.weight_pct),
    profit_loss: h.is_priced ? Number(h.profit_loss) : null,
    profit_loss_pct: h.is_priced ? Number(h.profit_loss_pct) : null,
    day_change_value: h.is_priced ? Number(h.day_change_value) : null,
  }))

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

  const columns = [
    { key: 'name', label: 'Name', sortable: true },
    { key: 'type', label: 'Type', sortable: true },
    {
      key: 'quantity',
      label: 'Qty',
      align: 'right',
      sortable: true,
      render: (row) => formatNumber(row.quantity, { maximumFractionDigits: 4 }),
    },
    {
      key: 'avg_buy_price',
      label: 'Avg Cost',
      align: 'right',
      sortable: true,
      render: (row) => formatNumber(row.avg_buy_price, { maximumFractionDigits: 2 }),
    },
    {
      key: 'current_value',
      label: 'Value',
      align: 'right',
      sortable: true,
      render: (row) => formatCurrency(row.current_value),
    },
    {
      key: 'profit_loss',
      label: 'P/L',
      align: 'right',
      sortable: true,
      pnl: true,
      render: (row) =>
        row.profit_loss == null ? (
          '—'
        ) : (
          <span className="block leading-tight">
            <span className="block">
              {row.profit_loss >= 0 ? '+' : ''}
              {formatCurrency(row.profit_loss)}
            </span>
            <span className="block text-xs opacity-70">{formatPercent(row.profit_loss_pct)}</span>
          </span>
        ),
    },
    {
      key: 'day_change_value',
      label: 'Day Chg',
      align: 'right',
      sortable: true,
      pnl: true,
      render: (row) =>
        row.day_change_value == null
          ? '—'
          : `${row.day_change_value >= 0 ? '+' : ''}${formatCurrency(row.day_change_value)}`,
    },
    {
      key: 'actions',
      label: '',
      align: 'right',
      render: (row) => (
        <div className="flex justify-end gap-2">
          <Button size="sm" variant="secondary" onClick={() => openSell(row, false)}>
            Sell
          </Button>
          <Button size="sm" variant="danger" onClick={() => openSell(row, true)}>
            Sell all
          </Button>
        </div>
      ),
    },
  ]

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

      <Card className="mb-6">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-sm font-medium uppercase tracking-wide text-text-secondary">
            Allocation
          </h2>
          <Tabs tabs={ALLOCATION_TABS} value={allocationBy} onChange={setAllocationBy} />
        </div>
        <AllocationDonut items={allocation?.items ?? []} loading={allocationLoading} />
      </Card>

      {!isLoading && rows.length === 0 ? (
        <div className="rounded border border-border bg-surface">
          <EmptyState
            title="No holdings yet"
            description="Deposit some cash, then buy your first stock or mutual fund."
            action={
              <Button size="sm" onClick={() => setBuyOpen(true)}>
                Buy an asset
              </Button>
            }
          />
        </div>
      ) : (
        <DataTable columns={columns} data={rows} loading={isLoading} getRowKey={(row) => row.holding_id} />
      )}

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
