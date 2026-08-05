import { Link } from 'react-router-dom'
import { Button, DataTable, EmptyState } from '../ui'
import { formatCurrency, formatNumber, formatPercent } from '../../utils/formatters'

export function toHoldingRows(holdings) {
  return holdings.map((h) => ({
    ...h,
    name: h.asset.name,
    type: h.asset.asset_type.replace('_', ' '),
    quantity: Number(h.quantity),
    avg_buy_price: Number(h.avg_buy_price),
    current_value: Number(h.current_value),
    weight_pct: Number(h.weight_pct),
    profit_loss: h.is_priced ? Number(h.profit_loss) : null,
    profit_loss_pct: h.is_priced ? Number(h.profit_loss_pct) : null,
    day_change_value: h.is_priced ? Number(h.day_change_value) : null,
  }))
}

export default function HoldingsTable({
  rows,
  loading,
  showType = true,
  onSell,
  onSellAll,
  emptyTitle = 'No holdings yet',
  emptyDescription = 'Deposit some cash, then buy your first asset.',
  emptyAction,
}) {
  const columns = [
    {
      key: 'name',
      label: 'Name',
      sortable: true,
      render: (row) => (
        <Link to={`/asset/${row.asset_id}`} className="hover:text-accent hover:underline">
          {row.name}
        </Link>
      ),
    },
    ...(showType ? [{ key: 'type', label: 'Type', sortable: true }] : []),
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
      key: 'current_value',
      label: 'Value',
      align: 'right',
      sortable: true,
      render: (row) => formatCurrency(row.current_value),
    },
    {
      key: 'profit_loss',
      label: 'P/L',
      align: 'right',
      sortable: true,
      pnl: true,
      render: (row) =>
        row.profit_loss == null ? (
          '—'
        ) : (
          <span className="block leading-tight">
            <span className="block">
              {row.profit_loss >= 0 ? '+' : ''}
              {formatCurrency(row.profit_loss)}
            </span>
            <span className="block text-xs opacity-70">{formatPercent(row.profit_loss_pct)}</span>
          </span>
        ),
    },
    {
      key: 'day_change_value',
      label: 'Day Chg',
      align: 'right',
      sortable: true,
      pnl: true,
      render: (row) =>
        row.day_change_value == null
          ? '—'
          : `${row.day_change_value >= 0 ? '+' : ''}${formatCurrency(row.day_change_value)}`,
    },
    {
      key: 'actions',
      label: '',
      align: 'right',
      render: (row) => (
        <div className="flex justify-end gap-2">
          <Button size="sm" variant="secondary" onClick={() => onSell?.(row)}>
            Sell
          </Button>
          <Button size="sm" variant="danger" onClick={() => onSellAll?.(row)}>
            Sell all
          </Button>
        </div>
      ),
    },
  ]

  if (!loading && rows.length === 0) {
    return (
      <div className="rounded border border-border bg-surface">
        <EmptyState title={emptyTitle} description={emptyDescription} action={emptyAction} />
      </div>
    )
  }

  return <DataTable columns={columns} data={rows} loading={loading} getRowKey={(row) => row.holding_id} />
}
