import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { assignTag, fetchTags, removeTag } from '../api/tags'

const TAGS_KEY = ['tags']

export function useTags() {
  return useQuery({ queryKey: TAGS_KEY, queryFn: fetchTags })
}

export function useAssignTag() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ holdingId, name }) => assignTag(holdingId, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TAGS_KEY })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
    },
  })
}

export function useRemoveTag() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ holdingId, tagId }) => removeTag(holdingId, tagId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
    },
  })
}
