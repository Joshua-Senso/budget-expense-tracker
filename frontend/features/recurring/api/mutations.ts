"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { QueryClient } from "@tanstack/react-query"

import { apiFetch } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"

import type { RecurringCreatePayload, RecurringExpense } from "../schemas"

function invalidateRecurringDependents(queryClient: QueryClient) {
  queryClient.invalidateQueries({ queryKey: queryKeys.recurring() })
  queryClient.invalidateQueries({ queryKey: queryKeys.recurringProjection() })
  queryClient.invalidateQueries({ queryKey: queryKeys.expenses() })
  queryClient.invalidateQueries({ queryKey: queryKeys.dashboard() })
}

function useCreateRecurringExpense() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: RecurringCreatePayload) =>
      apiFetch<RecurringExpense>("/recurring", { method: "POST", body: data }),
    onSuccess: () => invalidateRecurringDependents(queryClient),
  })
}

function useStopRecurringExpense() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, monthKey }: { id: string; monthKey: string }) =>
      apiFetch<null>(`/recurring/${id}/${monthKey}`, { method: "DELETE" }),
    onSuccess: () => invalidateRecurringDependents(queryClient),
  })
}

export { useCreateRecurringExpense, useStopRecurringExpense }
