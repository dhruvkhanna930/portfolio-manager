import { useState } from 'react'
import { Minus, Plus, Wallet } from 'lucide-react'
import { Button, Input, Modal, Skeleton, showToast } from '../ui'
import { useDeposit, useWallet, useWithdraw } from '../../hooks/useWallet'
import { formatCurrency } from '../../utils/formatters'
import { getApiErrorMessage } from '../../utils/apiError'

function CashModal({ open, onClose, title, actionLabel, onSubmit, submitting, balance }) {
  const [amount, setAmount] = useState('')

  const submit = (e) => {
    e.preventDefault()
    if (!(Number(amount) > 0)) return
    onSubmit(String(amount), () => setAmount(''))
  }

  return (
    <Modal
      open={open}
      onClose={() => {
        setAmount('')
        onClose()
      }}
      title={title}
    >
      <form onSubmit={submit} className="space-y-4">
        <Input
          id="cash_amount"
          label="Amount (₹)"
          type="number"
          step="any"
          autoFocus
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />
        <p className="text-xs text-text-muted">
          Current balance: {formatCurrency(balance)}. This is simulated cash — no real
          payment is processed.
        </p>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={!(Number(amount) > 0) || submitting}>
            {actionLabel}
          </Button>
        </div>
      </form>
    </Modal>
  )
}

export default function WalletBalance() {
  const { data: wallet, isLoading } = useWallet()
  const deposit = useDeposit()
  const withdraw = useWithdraw()
  const [depositOpen, setDepositOpen] = useState(false)
  const [withdrawOpen, setWithdrawOpen] = useState(false)

  const balance = wallet ? Number(wallet.balance) : 0

  const handleDeposit = (amount, reset) => {
    deposit.mutate(amount, {
      onSuccess: () => {
        showToast.success(`Deposited ${formatCurrency(Number(amount))}`)
        reset()
        setDepositOpen(false)
      },
      onError: (error) => showToast.error(getApiErrorMessage(error, 'Deposit failed')),
    })
  }

  const handleWithdraw = (amount, reset) => {
    withdraw.mutate(amount, {
      onSuccess: () => {
        showToast.success(`Withdrew ${formatCurrency(Number(amount))}`)
        reset()
        setWithdrawOpen(false)
      },
      onError: (error) => showToast.error(getApiErrorMessage(error, 'Withdrawal failed')),
    })
  }

  return (
    <>
      <div className="flex items-center gap-3 rounded border border-border bg-surface px-3 py-2">
        <Wallet className="h-4 w-4 shrink-0 text-accent" />
        <div className="min-w-0">
          <p className="text-[10px] font-medium uppercase tracking-wide text-text-secondary">
            Wallet
          </p>
          {isLoading ? (
            <Skeleton className="mt-0.5 h-4 w-20" />
          ) : (
            <p className="text-sm font-semibold tabular-nums text-text-primary">
              {formatCurrency(balance)}
            </p>
          )}
        </div>
        <div className="flex items-center gap-1">
          <Button size="sm" variant="secondary" onClick={() => setDepositOpen(true)} title="Deposit">
            <Plus className="h-3.5 w-3.5" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setWithdrawOpen(true)}
            title="Withdraw"
          >
            <Minus className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      <CashModal
        open={depositOpen}
        onClose={() => setDepositOpen(false)}
        title="Deposit cash"
        actionLabel="Deposit"
        onSubmit={handleDeposit}
        submitting={deposit.isPending}
        balance={balance}
      />
      <CashModal
        open={withdrawOpen}
        onClose={() => setWithdrawOpen(false)}
        title="Withdraw cash"
        actionLabel="Withdraw"
        onSubmit={handleWithdraw}
        submitting={withdraw.isPending}
        balance={balance}
      />
    </>
  )
}
