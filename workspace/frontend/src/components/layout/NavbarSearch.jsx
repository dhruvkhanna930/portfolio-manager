import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2, Search } from 'lucide-react'
import { useOwnSearch } from '../../hooks/useSearch'

function useDebounced(value, delay = 300) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

export default function NavbarSearch() {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const containerRef = useRef(null)
  const navigate = useNavigate()
  const debouncedQuery = useDebounced(query)

  const { data: results = [], isFetching } = useOwnSearch(debouncedQuery)

  useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = (asset) => {
    setQuery('')
    setOpen(false)
    navigate(`/asset/${asset.asset_id}`)
  }

  const showDropdown = open && query.trim().length > 0

  return (
    <div ref={containerRef} className="relative w-44">
      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
      <input
        type="search"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value)
          setOpen(true)
        }}
        onFocus={() => setOpen(true)}
        placeholder="Search stocks, funds, bonds..."
        className="h-9 w-full rounded border border-border bg-surface pl-9 pr-8 text-sm text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
      />
      {isFetching && (
        <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-text-muted" />
      )}

      {showDropdown && (
        <div className="absolute left-0 right-0 top-full z-50 mt-1 max-h-72 overflow-y-auto rounded border border-border bg-surface shadow-lg">
          {debouncedQuery.trim().length === 0 ? null : results.length === 0 && !isFetching ? (
            <p className="px-3 py-4 text-center text-sm text-text-muted">No matches in your assets</p>
          ) : (
            <ul>
              {results.map((asset) => (
                <li key={asset.asset_id}>
                  <button
                    type="button"
                    onClick={() => handleSelect(asset)}
                    className="flex w-full items-center justify-between gap-3 px-3 py-2.5 text-left hover:bg-surface-hover"
                  >
                    <span className="min-w-0">
                      <span className="block truncate text-sm text-text-primary">{asset.name}</span>
                      <span className="block text-xs text-text-muted">
                        {asset.symbol} · {asset.asset_type.replace('_', ' ')}
                      </span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
