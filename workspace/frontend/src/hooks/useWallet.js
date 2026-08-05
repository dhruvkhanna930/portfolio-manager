import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { depositCash, fetchWallet, withdrawCash } from '../api/wallet'

export const WALLET_KEY = ['wallet']

export function useWallet() {
  return useQuery({ queryKey: WALLET_KEY, queryFn: fetchWallet })
}

export function useDeposit() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: depositCash,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: WALLET_KEY }),
  })
}

export function useWithdraw() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: withdrawCash,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: WALLET_KEY }),
  })
}
