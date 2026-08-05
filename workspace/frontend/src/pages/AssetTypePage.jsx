import { useState } from 'react'
import { Plus } from 'lucide-react'
import { Button, showToast } from '../components/ui'
import HoldingsTable, { toHoldingRows } from '../components/portfolio/HoldingsTable'
import BuyModal from '../components/portfolio/BuyModal'
import SellModal from '../components/portfolio/SellModal'
import { useHoldings } from '../hooks/useHoldings'
import { useWallet } from '../hooks/useWallet'
import { useCreateSip, useCreateTransaction } from '../hooks/useTransactions'
import { getApiErrorMessage } from '../utils/apiError'
import { formatCurrency } from '../utils/formatters'

// The Stocks / Mutual Funds / Bonds segment pages are the same holdings table,
// just pre-filtered to one asset_type -- one component, mounted three times by
// App.jsx with different props, instead of three near-identical page files.
export default function AssetTypePage({ assetType, title, description, canBuy = true }) {
  const { data: holdings = [], isLoading } = useHoldings()
  const { data: wallet } = useWallet()
  const createTransaction = useCreateTransaction()
  const createSip = useCreateSip()

  const [buyOpen, setBuyOpen] = useState(false)
  const [sellTarget, setSellTarget] = useState(null)
  const [sellAll, setSellAll] = useState(false)

  const walletBalance = wallet ? Number(wallet.balance) : 0
  const rows = toHoldingRows(holdings).filter((h) => h.asset.asset_type === assetType)

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

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">{title}</h1>
          <p className="mt-1 text-text-secondary">{description}</p>
        </div>
        {canBuy && (
          <Button onClick={() => setBuyOpen(true)}>
            <Plus className="h-4 w-4" />
            Buy
          </Button>
        )}
      </div>

      <HoldingsTable
        rows={rows}
        loading={isLoading}
        showType={false}
        onSell={(row) => openSell(row, false)}
        onSellAll={(row) => openSell(row, true)}
        emptyTitle={`No ${title.toLowerCase()} yet`}
        emptyDescription={
          canBuy
            ? `Buy your first ${title.toLowerCase().replace(/s$/, '')} to see it here.`
            : `${title} are curated manually and don't have a live search yet -- see CLAUDE.md §4.1.`
        }
        emptyAction={
          canBuy && (
            <Button size="sm" onClick={() => setBuyOpen(true)}>
              Buy {title}
            </Button>
          )
        }
      />

      {canBuy && (
        <BuyModal
          open={buyOpen}
          onClose={() => setBuyOpen(false)}
          walletBalance={walletBalance}
          onBuy={handleBuy}
          onCreateSip={handleCreateSip}
          submitting={createTransaction.isPending || createSip.isPending}
        />
      )}

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
