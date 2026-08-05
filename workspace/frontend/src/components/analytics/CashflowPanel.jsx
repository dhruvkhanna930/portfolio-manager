/**
 * Cash flow: Sankey (where money went) + Waterfall (how the balance got here).
 *
 * Both read the same wallet ledger, so they must agree — the waterfall's final
 * bar is the wallet balance the API reports, not a figure re-derived here.
 */

import { Skeleton, Tabs } from '../ui'
import SankeyDiagram from '../charts/SankeyDiagram'
import WaterfallChart from '../charts/WaterfallChart'
import { useWallet } from '../../hooks/useWallet'
import { useTransactions } from '../../hooks/useTransactions'
import { buildCashflowSankey, buildCashflowWaterfall } from '../../utils/cashflow'
import { formatCurrency } from '../../utils/formatters'
import { useState } from 'react'

const VIEWS = [
  { key: 'sankey', label: 'Flow' },
  { key: 'waterfall', label: 'Breakdown' },
]

export default function CashflowPanel() {
  const [view, setView] = useState('sankey')
  const { data: wallet, isLoading: walletLoading } = useWallet()
  const { data: transactions = [], isLoading: txnLoading } = useTransactions()

  if (walletLoading || txnLoading) return <Skeleton className="h-80 w-full rounded" />
  if (!wallet) return null

  const entries = wallet.entries ?? []
  const balance = Number(wallet.balance ?? 0)
  const sankey = buildCashflowSankey({ entries, transactions, balance })
  const waterfall = buildCashflowWaterfall({ entries, balance })

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Tabs tabs={VIEWS} value={view} onChange={setView} className="w-fit" />
        <p className="text-sm text-text-secondary">
          Wallet balance{' '}
          <span className="tabular-nums text-text-primary">{formatCurrency(balance)}</span>
        </p>
      </div>

      {view === 'sankey' ? (
        <SankeyDiagram nodes={sankey.nodes} links={sankey.links} />
      ) : (
        <>
          <WaterfallChart steps={waterfall} />
          <p className="text-xs text-text-muted">
            Each bar is a category of cash movement from your ledger; the final bar is the balance
            they add up to.
          </p>
        </>
      )}
    </div>
  )
}
