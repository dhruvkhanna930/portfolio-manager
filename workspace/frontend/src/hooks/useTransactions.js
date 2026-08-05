import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createSip, createTransaction, fetchTransactions } from '../api/transactions'

const TRANSACTIONS_KEY = ['transactions']

// A BUY/SELL changes holdings, the wallet, summary totals and allocation all at
// once -- invalidate the whole set rather than trying to patch each cache.
function invalidateAll(queryClient) {
  ;[
    TRANSACTIONS_KEY,
    ['holdings'],
    ['wallet'],
    ['portfolio-summary'],
    ['portfolio-allocation'],
    ['sips'],
  ].forEach((queryKey) => queryClient.invalidateQueries({ queryKey }))
}

export function useTransactions() {
  return useQuery({ queryKey: TRANSACTIONS_KEY, queryFn: fetchTransactions })
}

export function useCreateTransaction() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createTransaction,
    onSuccess: () => invalidateAll(queryClient),
  })
}

export function useCreateSip() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createSip,
    onSuccess: () => invalidateAll(queryClient),
  })
}
