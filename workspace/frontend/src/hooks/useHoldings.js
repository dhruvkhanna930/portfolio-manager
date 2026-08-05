import { useQuery } from '@tanstack/react-query'
import { fetchHoldings } from '../api/portfolio'

const HOLDINGS_KEY = ['holdings']

// v2: read-only. Holdings change as a side effect of transactions, so the
// mutation hooks live in useTransactions.js and invalidate this key.
export function useHoldings() {
  return useQuery({ queryKey: HOLDINGS_KEY, queryFn: fetchHoldings })
}
