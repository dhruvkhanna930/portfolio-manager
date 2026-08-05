import { useMemo, useState } from 'react'
import { ArrowUp, ArrowDown, ChevronsUpDown } from 'lucide-react'
import { cn } from '../../utils/cn'
import { formatNumber } from '../../utils/formatters'
import Skeleton from './Skeleton'
import EmptyState from './EmptyState'

export default function DataTable({
  columns,
  data = [],
  loading = false,
  getRowKey = (row, index) => row.id ?? index,
  emptyMessage = 'No data yet',
  className,
}) {
  const [sort, setSort] = useState(null)

  const sortedData = useMemo(() => {
    if (!sort) return data
    const { key, direction } = sort
    const sorted = [...data].sort((a, b) => {
      const av = a[key]
      const bv = b[key]
      if (typeof av === 'number' && typeof bv === 'number') return av - bv
      return String(av ?? '').localeCompare(String(bv ?? ''))
    })
    return direction === 'asc' ? sorted : sorted.reverse()
  }, [data, sort])

  const toggleSort = (key) => {
    setSort((current) => {
      if (current?.key !== key) return { key, direction: 'asc' }
      if (current.direction === 'asc') return { key, direction: 'desc' }
      return null
    })
  }

  return (
    <div className={cn('overflow-x-auto rounded border border-border', className)}>
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border bg-surface">
            {columns.map((col) => (
              <th
                key={col.key}
                className={cn(
                  'select-none whitespace-nowrap px-4 py-3 text-xs font-medium uppercase tracking-wide text-text-secondary',
                  col.align === 'right' ? 'text-right' : 'text-left',
                  col.sortable && 'cursor-pointer hover:text-text-primary'
                )}
                onClick={() => col.sortable && toggleSort(col.key)}
              >
                <span
                  className={cn(
                    'inline-flex items-center gap-1',
                    col.align === 'right' && 'flex-row-reverse'
                  )}
                >
                  {col.label}
                  {col.sortable &&
                    (sort?.key === col.key ? (
                      sort.direction === 'asc' ? (
                        <ArrowUp className="h-3 w-3" />
                      ) : (
                        <ArrowDown className="h-3 w-3" />
                      )
                    ) : (
                      <ChevronsUpDown className="h-3 w-3 opacity-40" />
                    ))}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading &&
            Array.from({ length: 4 }).map((_, i) => (
              <tr key={i} className="border-b border-border last:border-0">
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-3">
                    <Skeleton className="h-4 w-full max-w-[120px]" />
                  </td>
                ))}
              </tr>
            ))}

          {!loading && sortedData.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="p-0">
                <EmptyState title={emptyMessage} />
              </td>
            </tr>
          )}

          {!loading &&
            sortedData.map((row, index) => (
              <tr
                key={getRowKey(row, index)}
                className="border-b border-border last:border-0 hover:bg-surface-hover"
              >
                {columns.map((col) => {
                  const rawValue = row[col.key]
                  let content = col.render ? col.render(row) : rawValue
                  let toneClass = ''

                  if (col.pnl && typeof rawValue === 'number') {
                    toneClass = rawValue >= 0 ? 'text-positive' : 'text-negative'
                    if (!col.render) {
                      content = `${rawValue >= 0 ? '+' : ''}${formatNumber(rawValue, {
                        maximumFractionDigits: 2,
                      })}`
                    }
                  }

                  return (
                    <td
                      key={col.key}
                      className={cn(
                        'whitespace-nowrap px-4 py-3 tabular-nums text-text-primary',
                        col.align === 'right' ? 'text-right' : 'text-left',
                        toneClass
                      )}
                    >
                      {content}
                    </td>
                  )
                })}
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  )
}
