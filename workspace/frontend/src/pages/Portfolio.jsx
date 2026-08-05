import { useState } from 'react'
import { Plus } from 'lucide-react'
import { Button, DataTable, EmptyState, Modal, showToast } from '../components/ui'
import AddEditHoldingModal from '../components/portfolio/AddEditHoldingModal'
import { useCreateHolding, useDeleteHolding, useHoldings, useUpdateHolding } from '../hooks/useHoldings'
import { useAssets } from '../hooks/useAssets'
import { getApiErrorMessage } from '../utils/apiError'
import { formatNumber } from '../utils/formatters'

export default function Portfolio() {
  const { data: holdings = [], isLoading } = useHoldings()
  const { data: assets = [] } = useAssets()
  const createHolding = useCreateHolding()
  const updateHolding = useUpdateHolding()
  const deleteHolding = useDeleteHolding()

  const [modalOpen, setModalOpen] = useState(false)
  const [editingHolding, setEditingHolding] = useState(null)
  const [deletingHolding, setDeletingHolding] = useState(null)

  const rows = holdings.map((h) => ({
    ...h,
    name: h.asset.name,
    type: h.asset.asset_type.replace('_', ' '),
    quantity: Number(h.quantity),
    avg_buy_price: Number(h.avg_buy_price),
  }))

  const openAddModal = () => {
    setEditingHolding(null)
    setModalOpen(true)
  }

  const openEditModal = (holding) => {
    setEditingHolding(holding)
    setModalOpen(true)
  }

  const handleSubmit = (payload) => {
    if (editingHolding) {
      updateHolding.mutate(
        { holdingId: editingHolding.holding_id, payload },
        {
          onSuccess: () => {
            showToast.success('Holding updated')
            setModalOpen(false)
          },
          onError: (error) => showToast.error(getApiErrorMessage(error, 'Failed to update holding')),
        }
      )
    } else {
      createHolding.mutate(payload, {
        onSuccess: () => {
          showToast.success('Holding added')
          setModalOpen(false)
        },
        onError: (error) => showToast.error(getApiErrorMessage(error, 'Failed to add holding')),
      })
    }
  }

  const confirmDelete = () => {
    if (!deletingHolding) return
    deleteHolding.mutate(deletingHolding.holding_id, {
      onSuccess: () => {
        showToast.success('Holding deleted')
        setDeletingHolding(null)
      },
      onError: (error) => {
        showToast.error(getApiErrorMessage(error, 'Failed to delete holding'))
        setDeletingHolding(null)
      },
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
      key: 'actions',
      label: '',
      align: 'right',
      render: (row) => (
        <div className="flex justify-end gap-2">
          <Button size="sm" variant="secondary" onClick={() => openEditModal(row)}>
            Edit
          </Button>
          <Button size="sm" variant="danger" onClick={() => setDeletingHolding(row)}>
            Delete
          </Button>
        </div>
      ),
    },
  ]

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">My Portfolio</h1>
          <p className="mt-1 text-text-secondary">Your stocks, mutual funds, and bonds.</p>
        </div>
        <Button onClick={openAddModal}>
          <Plus className="h-4 w-4" />
          Add Holding
        </Button>
      </div>

      {!isLoading && rows.length === 0 ? (
        <div className="rounded border border-border bg-surface">
          <EmptyState
            title="No holdings yet"
            description="Add your first stock, mutual fund, or bond to get started."
            action={
              <Button size="sm" onClick={openAddModal}>
                Add holding
              </Button>
            }
          />
        </div>
      ) : (
        <DataTable columns={columns} data={rows} loading={isLoading} getRowKey={(row) => row.holding_id} />
      )}

      <AddEditHoldingModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSubmit={handleSubmit}
        assets={assets}
        holding={editingHolding}
        submitting={createHolding.isPending || updateHolding.isPending}
      />

      <Modal open={Boolean(deletingHolding)} onClose={() => setDeletingHolding(null)} title="Delete holding">
        <p className="text-sm text-text-secondary">
          Remove {deletingHolding?.asset?.name} from your portfolio? This can't be undone.
        </p>
        <div className="mt-6 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setDeletingHolding(null)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={confirmDelete} disabled={deleteHolding.isPending}>
            Delete
          </Button>
        </div>
      </Modal>
    </div>
  )
}
