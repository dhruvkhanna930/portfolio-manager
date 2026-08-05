import { useState } from 'react'
import { Plus } from 'lucide-react'
import { Button, EmptyState, showToast } from '../components/ui'
import BuyModal from '../components/portfolio/BuyModal'
import SipCard from '../components/sips/SipCard'
import { useSips } from '../hooks/useSips'
import { useWallet } from '../hooks/useWallet'
import { useCreateSip } from '../hooks/useTransactions'
import { getApiErrorMessage } from '../utils/apiError'

export default function Sips() {
  const { data: sips = [], isLoading } = useSips()
  const { data: wallet } = useWallet()
  const createSip = useCreateSip()
  const [newSipOpen, setNewSipOpen] = useState(false)

  const walletBalance = wallet ? Number(wallet.balance) : 0

  const handleCreateSip = (payload) => {
    createSip.mutate(payload, {
      onSuccess: () => {
        showToast.success('SIP plan created — no cash debited')
        setNewSipOpen(false)
      },
      onError: (error) => showToast.error(getApiErrorMessage(error, 'Could not create SIP')),
    })
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">SIPs</h1>
          <p className="mt-1 text-text-secondary">
            Simulated SIP plans with a projected growth chart — no auto-debit, no real execution.
          </p>
        </div>
        <Button onClick={() => setNewSipOpen(true)}>
          <Plus className="h-4 w-4" />
          New SIP
        </Button>
      </div>

      {!isLoading && sips.length === 0 ? (
        <div className="rounded border border-border bg-surface">
          <EmptyState
            title="No SIP plans yet"
            description="Create a simulated SIP for a mutual fund to see its projected growth."
            action={
              <Button size="sm" onClick={() => setNewSipOpen(true)}>
                Create a SIP
              </Button>
            }
          />
        </div>
      ) : (
        <div className="space-y-4">
          {sips.map((sip) => (
            <SipCard key={sip.sip_id} sip={sip} />
          ))}
        </div>
      )}

      <BuyModal
        open={newSipOpen}
        onClose={() => setNewSipOpen(false)}
        walletBalance={walletBalance}
        onBuy={() => {}}
        onCreateSip={handleCreateSip}
        submitting={createSip.isPending}
        initialAssetType="MUTUAL_FUND"
        initialMode="SIP"
      />
    </div>
  )
}
