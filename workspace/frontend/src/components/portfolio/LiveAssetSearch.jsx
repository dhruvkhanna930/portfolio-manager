import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Loader2, Search } from 'lucide-react'
import { searchLiveAssets } from '../../api/assets'
import { Tabs } from '../ui'

const TYPE_TABS = [
  { key: 'STOCK', label: 'Stocks' },
  { key: 'MUTUAL_FUND', label: 'Mutual Funds' },
]

function useDebounced(value, delay = 350) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

export default function LiveAssetSearch({ assetType, onAssetTypeChange, onSelect }) {
  const [query, setQuery] = useState('')
  const debouncedQuery = useDebounced(query)

  const { data: results = [], isFetching } = useQuery({
    queryKey: ['asset-search', assetType, debouncedQuery],
    queryFn: () => searchLiveAssets(debouncedQuery, assetType),
    enabled: debouncedQuery.trim().length >= 2,
  })

  return (
    <div className="space-y-3">
      <Tabs
        tabs={TYPE_TABS}
        value={assetType}
        onChange={(next) => {
          onAssetTypeChange(next)
          setQuery('')
        }}
      />

      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
        <input
          autoFocus
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={assetType === 'STOCK' ? 'Search e.g. Infosys, TCS…' : 'Search e.g. Parag Parikh…'}
          className="h-10 w-full rounded border border-border bg-bg pl-9 pr-9 text-sm text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none"
        />
        {isFetching && (
          <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-text-muted" />
        )}
      </div>

      <div className="max-h-56 overflow-y-auto rounded border border-border">
        {debouncedQuery.trim().length < 2 ? (
          <p className="px-3 py-6 text-center text-sm text-text-muted">
            Type at least 2 characters to search
          </p>
        ) : results.length === 0 && !isFetching ? (
          <p className="px-3 py-6 text-center text-sm text-text-muted">No matches found</p>
        ) : (
          <ul>
            {results.map((result) => (
              <li key={`${result.asset_type}-${result.symbol}`}>
                <button
                  type="button"
                  onClick={() => onSelect(result)}
                  className="flex w-full items-center justify-between gap-3 px-3 py-2.5 text-left hover:bg-surface-hover"
                >
                  <span className="min-w-0">
                    <span className="block truncate text-sm text-text-primary">{result.name}</span>
                    <span className="block text-xs text-text-muted">
                      {result.symbol}
                      {result.exchange ? ` · ${result.exchange}` : ''}
                    </span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
