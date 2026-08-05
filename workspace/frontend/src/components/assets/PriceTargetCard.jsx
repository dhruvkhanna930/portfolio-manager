/**
 * Set a price target on this asset (§15.5).
 *
 * The target is stored; whether it has been *hit* is never stored — that's
 * recomputed from the live price every time the alerts panel opens, so a target
 * can't get stuck in a "fired" state after the price moves back.
 *
 * The card is explicit that this notifies in-app only. There is no login and no
 * contact details in this app, so there is nowhere to send a push or an email,
 * and pretending otherwise would be a lie about what the feature does.
 */

import { useState } from 'react'
import { Bell, Trash2 } from 'lucide-react'

import { Button, Card, Input, Select, showToast } from '../ui'
import {
  useCreatePriceTarget,
  useDeletePriceTarget,
  usePriceTargets,
} from '../../hooks/useVisualAnalytics'
import { getApiErrorMessage } from '../../utils/apiError'
import { formatCurrency } from '../../utils/formatters'

const DIRECTIONS = [
  { value: 'ABOVE', label: 'Rises to or above' },
  { value: 'BELOW', label: 'Falls to or below' },
]

export default function PriceTargetCard({ assetId, asset }) {
  const { data: targets = [] } = usePriceTargets()
  const create = useCreatePriceTarget()
  const remove = useDeletePriceTarget()
  const [price, setPrice] = useState('')
  const [direction, setDirection] = useState('ABOVE')

  const mine = targets.filter((t) => t.asset_id === assetId)
  const current = asset?.current_price != null ? Number(asset.current_price) : null

  const submit = (e) => {
    e.preventDefault()
    create.mutate(
      { asset_id: assetId, target_price: price, direction },
      {
        onSuccess: () => {
          showToast.success('Price target set')
          setPrice('')
        },
        onError: (error) => showToast.error(getApiErrorMessage(error, 'Could not set target')),
      }
    )
  }

  return (
    <Card>
      <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-text-secondary">
        Price alerts
      </h2>

      {mine.length > 0 && (
        <ul className="mb-4 space-y-2">
          {mine.map((target) => {
            const want = Number(target.target_price)
            const hit =
              current != null && (target.direction === 'ABOVE' ? current >= want : current <= want)
            return (
              <li
                key={target.target_id}
                className="flex items-center gap-2.5 rounded border border-border bg-bg px-3 py-2 text-sm"
              >
                <Bell className={`h-4 w-4 shrink-0 ${hit ? 'text-accent' : 'text-text-muted'}`} />
                <span className="min-w-0 flex-1 text-text-secondary">
                  {target.direction === 'ABOVE' ? 'Above' : 'Below'}{' '}
                  <span className="tabular-nums text-text-primary">{formatCurrency(want)}</span>
                  {hit && <span className="ml-2 text-xs text-accent">reached</span>}
                </span>
                <button
                  type="button"
                  onClick={() =>
                    remove.mutate(target.target_id, {
                      onSuccess: () => showToast.success('Target removed'),
                    })
                  }
                  className="shrink-0 rounded p-1 text-text-muted hover:bg-surface-hover hover:text-negative"
                  aria-label="Remove price target"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </li>
            )
          })}
        </ul>
      )}

      <form onSubmit={submit} className="space-y-3">
        <Select
          id="target_direction"
          label="Tell me when the price"
          options={DIRECTIONS}
          value={direction}
          onChange={(e) => setDirection(e.target.value)}
        />
        <Input
          id="target_price"
          label="Target price (₹)"
          type="number"
          step="any"
          min="0"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
          placeholder={current != null ? String(current) : ''}
        />
        <Button type="submit" size="sm" disabled={!(Number(price) > 0) || create.isPending}>
          <Bell className="h-4 w-4" />
          Set target
        </Button>
      </form>

      <p className="mt-3 text-xs text-text-muted">
        Shows up in the bell menu inside this app when the condition is met. Nothing is emailed or
        pushed — this app has no login or contact details to send to.
      </p>
    </Card>
  )
}
