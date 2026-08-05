import { Link } from 'react-router-dom'
import { DataTable } from '../ui'
import Sparkline from '../charts/Sparkline'
import { formatCurrency, formatPercent } from '../../utils/formatters'

export default function CondensedHoldingsTable({ rows, loading }) {
  const columns = [
    {
      key: 'name',
      label: 'Name',
      render: (row) => (
        <Link to={`/asset/${row.asset_id}`} className="hover:text-accent hover:underline">
          {row.name}
        </Link>
      ),
    },
    {
      key: 'current_value',
      label: 'Value',
      align: 'right',
      render: (row) => formatCurrency(row.current_value),
    },
    {
      key: 'profit_loss_pct',
      label: 'P/L %',
      align: 'right',
      render: (row) =>
        row.profit_loss_pct == null ? (
          '—'
        ) : (
          <span className={row.profit_loss_pct >= 0 ? 'text-positive' : 'text-negative'}>
            {formatPercent(row.profit_loss_pct)}
          </span>
        ),
    },
    {
      key: 'trend',
      label: '1M Trend',
      align: 'right',
      render: (row) => (
        <div className="flex justify-end">
          <Sparkline assetId={row.asset_id} />
        </div>
      ),
    },
  ]

  return (
    <DataTable
      columns={columns}
      data={rows}
      loading={loading}
      getRowKey={(row) => row.holding_id}
      emptyMessage="No holdings yet"
    />
  )
}
