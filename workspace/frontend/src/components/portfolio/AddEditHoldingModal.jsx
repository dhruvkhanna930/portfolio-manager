import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import Modal from '../ui/Modal'
import Input from '../ui/Input'
import Select from '../ui/Select'
import Button from '../ui/Button'

const holdingSchema = z.object({
  asset_id: z.coerce.number().positive('Select an asset'),
  quantity: z.coerce.number().min(0, 'Quantity must be 0 or greater'),
  avg_buy_price: z.coerce.number().positive('Average cost must be greater than 0'),
  first_bought: z.string().optional(),
  notes: z.string().optional(),
})

const EMPTY_VALUES = { asset_id: '', quantity: '', avg_buy_price: '', first_bought: '', notes: '' }

export default function AddEditHoldingModal({ open, onClose, onSubmit, assets, holding, submitting }) {
  const isEdit = Boolean(holding)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(holdingSchema),
    defaultValues: EMPTY_VALUES,
  })

  useEffect(() => {
    if (!open) return
    if (holding) {
      reset({
        asset_id: holding.asset_id,
        quantity: holding.quantity,
        avg_buy_price: holding.avg_buy_price,
        first_bought: holding.first_bought || '',
        notes: holding.notes || '',
      })
    } else {
      reset(EMPTY_VALUES)
    }
  }, [open, holding, reset])

  const assetOptions = [
    { value: '', label: 'Select an asset...' },
    ...assets.map((a) => ({ value: a.asset_id, label: `${a.symbol} — ${a.name}` })),
  ]

  const submitForm = (values) => {
    onSubmit({
      ...(isEdit ? {} : { asset_id: values.asset_id }),
      quantity: String(values.quantity),
      avg_buy_price: String(values.avg_buy_price),
      first_bought: values.first_bought || null,
      notes: values.notes || null,
    })
  }

  return (
    <Modal open={open} onClose={onClose} title={isEdit ? 'Edit Holding' : 'Add Holding'}>
      <form onSubmit={handleSubmit(submitForm)} className="space-y-4">
        <Select
          id="asset_id"
          label="Asset"
          options={assetOptions}
          disabled={isEdit}
          error={errors.asset_id?.message}
          {...register('asset_id')}
        />
        <div className="grid grid-cols-2 gap-4">
          <Input
            id="quantity"
            label="Quantity"
            type="number"
            step="any"
            error={errors.quantity?.message}
            {...register('quantity')}
          />
          <Input
            id="avg_buy_price"
            label="Avg Cost (₹)"
            type="number"
            step="any"
            error={errors.avg_buy_price?.message}
            {...register('avg_buy_price')}
          />
        </div>
        <Input
          id="first_bought"
          label="First bought"
          type="date"
          error={errors.first_bought?.message}
          {...register('first_bought')}
        />
        <Input
          id="notes"
          label="Notes"
          placeholder="Optional"
          error={errors.notes?.message}
          {...register('notes')}
        />
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {isEdit ? 'Save changes' : 'Add holding'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
