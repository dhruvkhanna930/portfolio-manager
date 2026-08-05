import { useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { Button, Input, Modal, Select, Tabs } from '../ui'
import LiveAssetSearch from './LiveAssetSearch'
import { resolveAsset } from '../../api/assets'
import { formatCurrency } from '../../utils/formatters'
import { getApiErrorMessage } from '../../utils/apiError'

const MODE_TABS = [
  { key: 'LUMPSUM', label: 'Lumpsum' },
  { key: 'SIP', label: 'SIP' },
]

const FREQUENCIES = [
  { value: 'MONTHLY', label: 'Monthly' },
  { value: 'WEEKLY', label: 'Weekly' },
  { value: 'DAILY', label: 'Daily' },
  { value: 'QUARTERLY', label: 'Quarterly' },
]

const today = () => new Date().toISOString().slice(0, 10)

export default function BuyModal({ open, onClose, walletBalance, onBuy, onCreateSip, submitting }) {
  const [assetType, setAssetType] = useState('STOCK')
  const [selected, setSelected] = useState(null)
  const [mode, setMode] = useState('LUMPSUM')
  const [resolveError, setResolveError] = useState(null)

  const [quantity, setQuantity] = useState('')
  const [price, setPrice] = useState('')
  const [fees, setFees] = useState('0')
  const [txnDate, setTxnDate] = useState(today)

  const [sipAmount, setSipAmount] = useState('')
  const [frequency, setFrequency] = useState('MONTHLY')
  const [startDate, setStartDate] = useState(today)

  const resolve = useMutation({ mutationFn: resolveAsset })

  useEffect(() => {
    if (!open) {
      setAssetType('STOCK')
      setSelected(null)
      setMode('LUMPSUM')
      setResolveError(null)
      setQuantity('')
      setPrice('')
      setFees('0')
      setTxnDate(today())
      setSipAmount('')
      setFrequency('MONTHLY')
      setStartDate(today())
      resolve.reset()
    }
  }, [open])

  const handleSelect = (result) => {
    setResolveError(null)
    resolve.mutate(
      { symbol: result.symbol, asset_type: result.asset_type, name: result.name },
      {
        onSuccess: (resolved) => {
          setSelected(resolved)
          setMode(resolved.asset_type === 'MUTUAL_FUND' ? 'LUMPSUM' : 'LUMPSUM')
        },
        onError: (error) => setResolveError(getApiErrorMessage(error, 'Could not add this asset')),
      }
    )
  }

  const cost = (Number(quantity) || 0) * (Number(price) || 0) + (Number(fees) || 0)
  const insufficient = cost > walletBalance
  const canBuy = Number(quantity) > 0 && Number(price) > 0 && !insufficient
  const canSip = Number(sipAmount) > 0 && Boolean(startDate)

  const submitBuy = (e) => {
    e.preventDefault()
    if (!canBuy) return
    onBuy({
      asset_id: selected.asset_id,
      txn_type: 'BUY',
      quantity: String(quantity),
      price: String(price),
      fees: String(fees || 0),
      txn_date: txnDate,
    })
  }

  const submitSip = (e) => {
    e.preventDefault()
    if (!canSip) return
    onCreateSip({
      asset_id: selected.asset_id,
      amount: String(sipAmount),
      frequency,
      start_date: startDate,
    })
  }

  const isMutualFund = selected?.asset_type === 'MUTUAL_FUND'

  return (
    <Modal open={open} onClose={onClose} title={selected ? 'Buy' : 'Search an asset'}>
      {!selected ? (
        <div className="space-y-3">
          <LiveAssetSearch
            assetType={assetType}
            onAssetTypeChange={setAssetType}
            onSelect={handleSelect}
          />
          {resolve.isPending && (
            <p className="flex items-center gap-2 text-sm text-text-secondary">
              <Loader2 className="h-4 w-4 animate-spin" />
              Adding asset and backfilling price history…
            </p>
          )}
          {resolveError && <p className="text-sm text-negative">{resolveError}</p>}
          <p className="text-xs text-text-muted">
            Bonds aren't searchable — there's no live search API for Indian retail bonds, so
            they stay a curated list.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-text-primary">{selected.name}</p>
              <p className="text-xs text-text-muted">
                {selected.symbol}
                {selected.created ? ` · ${selected.history_rows_added} history rows added` : ''}
              </p>
            </div>
            <Button size="sm" variant="ghost" onClick={() => setSelected(null)}>
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
          </div>

          {isMutualFund && (
            <Tabs tabs={MODE_TABS} value={mode} onChange={setMode} />
          )}

          {isMutualFund && mode === 'SIP' ? (
            <form onSubmit={submitSip} className="space-y-4">
              <Input
                id="sip_amount"
                label="Amount per instalment (₹)"
                type="number"
                step="any"
                value={sipAmount}
                onChange={(e) => setSipAmount(e.target.value)}
              />
              <div className="grid grid-cols-2 gap-4">
                <Select
                  id="frequency"
                  label="Frequency"
                  options={FREQUENCIES}
                  value={frequency}
                  onChange={(e) => setFrequency(e.target.value)}
                />
                <Input
                  id="start_date"
                  label="Start date"
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </div>
              <p className="text-xs text-text-muted">
                SIPs are simulated — this creates a plan only. No cash is debited and no
                transaction is recorded until an instalment is actually executed.
              </p>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="secondary" onClick={onClose}>
                  Cancel
                </Button>
                <Button type="submit" disabled={!canSip || submitting}>
                  Create SIP
                </Button>
              </div>
            </form>
          ) : (
            <form onSubmit={submitBuy} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Input
                  id="quantity"
                  label={isMutualFund ? 'Units' : 'Quantity'}
                  type="number"
                  step="any"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                />
                <Input
                  id="price"
                  label={isMutualFund ? 'NAV (₹)' : 'Price (₹)'}
                  type="number"
                  step="any"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Input
                  id="fees"
                  label="Fees (₹)"
                  type="number"
                  step="any"
                  value={fees}
                  onChange={(e) => setFees(e.target.value)}
                />
                <Input
                  id="txn_date"
                  label="Date"
                  type="date"
                  value={txnDate}
                  onChange={(e) => setTxnDate(e.target.value)}
                />
              </div>

              <div className="rounded border border-border bg-bg p-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-text-secondary">Total cost</span>
                  <span className="tabular-nums text-text-primary">{formatCurrency(cost)}</span>
                </div>
                <div className="mt-1 flex items-center justify-between">
                  <span className="text-text-secondary">Wallet balance</span>
                  <span
                    className={`tabular-nums ${insufficient ? 'text-negative' : 'text-text-primary'}`}
                  >
                    {formatCurrency(walletBalance)}
                  </span>
                </div>
                {insufficient && (
                  <p className="mt-2 text-xs text-negative">
                    Not enough cash — deposit {formatCurrency(cost - walletBalance)} more to
                    place this order.
                  </p>
                )}
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="secondary" onClick={onClose}>
                  Cancel
                </Button>
                <Button type="submit" disabled={!canBuy || submitting}>
                  Buy
                </Button>
              </div>
            </form>
          )}
        </div>
      )}
    </Modal>
  )
}
