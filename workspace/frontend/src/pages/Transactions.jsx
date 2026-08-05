import { Badge, DataTable } from '../components/ui'
import { useTransactions } from '../hooks/useTransactions'
import { formatCurrency, formatNumber } from '../utils/formatters'

const TYPE_TONE = { BUY: 'accent', SELL: 'negative', DIVIDEND: 'positive' }

export default function Transactions() {
  const { data: transactions = [], isLoading } = useTransactions()

  const rows = transactions.map((t) => ({
    ...t,
    name: t.asset?.name ?? '—',
    quantity: Number(t.quantity),
    price: Number(t.price),
    fees: Number(t.fees ?? 0),
  }))

  const columns = [
    { key: 'txn_date', label: 'Date', sortable: true },
    { key: 'name', label: 'Asset', sortable: true },
    {
      key: 'txn_type',
      label: 'Type',
      sortable: true,
      render: (row) => <Badge tone={TYPE_TONE[row.txn_type] ?? 'neutral'}>{row.txn_type}</Badge>,
    },
    {
      key: 'quantity',
      label: 'Qty',
      align: 'right',
      sortable: true,
      render: (row) => formatNumber(row.quantity, { maximumFractionDigits: 4 }),
    },
    {
      key: 'price',
      label: 'Price',
      align: 'right',
      sortable: true,
      render: (row) => formatCurrency(row.price),
    },
    {
      key: 'fees',
      label: 'Fees',
      align: 'right',
      sortable: true,
      render: (row) => formatCurrency(row.fees),
    },
  ]

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-text-primary">Transactions</h1>
        <p className="mt-1 text-text-secondary">
          Every buy, sell, and dividend. Holdings and your wallet are derived from this history.
        </p>
      </div>

      <DataTable
        columns={columns}
        data={rows}
        loading={isLoading}
        getRowKey={(row) => row.transaction_id}
        emptyMessage="No transactions yet"
      />
    </div>
  )
}
