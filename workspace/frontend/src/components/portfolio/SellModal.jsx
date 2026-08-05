import { useEffect, useState } from 'react'
import { Button, Input, Modal } from '../ui'
import { formatCurrency, formatNumber } from '../../utils/formatters'

const today = () => new Date().toISOString().slice(0, 10)

export default function SellModal({ open, onClose, holding, sellAll = false, onSell, submitting }) {
  const heldQty = holding ? Number(holding.quantity) : 0
  const [quantity, setQuantity] = useState('')
  const [price, setPrice] = useState('')
  const [fees, setFees] = useState('0')
  const [txnDate, setTxnDate] = useState(today)

  useEffect(() => {
    if (open && holding) {
      setQuantity(sellAll ? String(heldQty) : '')
      setPrice(holding.current_price ? String(Number(holding.current_price)) : '')
      setFees('0')
      setTxnDate(today())
    }
  }, [open, holding, sellAll])

  if (!holding) return null

  const qtyNum = Number(quantity) || 0
  const exceedsHeld = qtyNum > heldQty
  const proceeds = qtyNum * (Number(price) || 0) - (Number(fees) || 0)
  const avgCost = Number(holding.avg_buy_price)
  const estRealised = qtyNum * ((Number(price) || 0) - avgCost) - (Number(fees) || 0)
  const canSell = qtyNum > 0 && Number(price) > 0 && !exceedsHeld

  const submit = (e) => {
    e.preventDefault()
    if (!canSell) return
    onSell({
      asset_id: holding.asset_id,
      txn_type: 'SELL',
      quantity: String(quantity),
      price: String(price),
      fees: String(fees || 0),
      txn_date: txnDate,
    })
  }

  return (
    <Modal open={open} onClose={onClose} title={sellAll ? 'Sell all' : 'Sell'}>
      <form onSubmit={submit} className="space-y-4">
        <div>
          <p className="text-sm font-medium text-text-primary">{holding.asset?.name}</p>
          <p className="text-xs text-text-muted">
            You hold {formatNumber(heldQty, { maximumFractionDigits: 4 })} units @ avg{' '}
            {formatCurrency(avgCost)}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Input
            id="sell_quantity"
            label="Quantity"
            type="number"
            step="any"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            error={exceedsHeld ? `You only hold ${formatNumber(heldQty, { maximumFractionDigits: 4 })}` : undefined}
          />
          <Input
            id="sell_price"
            label="Price (₹)"
            type="number"
            step="any"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Input
            id="sell_fees"
            label="Fees (₹)"
            type="number"
            step="any"
            value={fees}
            onChange={(e) => setFees(e.target.value)}
          />
          <Input
            id="sell_date"
            label="Date"
            type="date"
            value={txnDate}
            onChange={(e) => setTxnDate(e.target.value)}
          />
        </div>

        <div className="rounded border border-border bg-bg p-3 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-text-secondary">Proceeds to wallet</span>
            <span className="tabular-nums text-text-primary">{formatCurrency(proceeds)}</span>
          </div>
          <div className="mt-1 flex items-center justify-between">
            <span className="text-text-secondary">Est. realised P/L</span>
            <span
              className={`tabular-nums ${estRealised >= 0 ? 'text-positive' : 'text-negative'}`}
            >
              {estRealised >= 0 ? '+' : ''}
              {formatCurrency(estRealised)}
            </span>
          </div>
          {qtyNum > 0 && qtyNum === heldQty && (
            <p className="mt-2 text-xs text-text-muted">
              This sells your entire position — the holding will disappear from your portfolio.
            </p>
          )}
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="danger" disabled={!canSell || submitting}>
            Sell
          </Button>
        </div>
      </form>
    </Modal>
  )
}
