"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { QueryClient } from "@tanstack/react-query"

import { apiFetch } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"

import type { Expense, ExpensePayload } from "../schemas"

function invalidateExpenseDependents(queryClient: QueryClient) {
  queryClient.invalidateQueries({ queryKey: queryKeys.expenses() })
  queryClient.invalidateQueries({ queryKey: queryKeys.dashboard() })
}

function useCreateExpense() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ExpensePayload) =>
      apiFetch<Expense>("/expenses", { method: "POST", body: data }),
    onSuccess: () => invalidateExpenseDependents(queryClient),
  })
}

function useUpdateExpense() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ExpensePayload> }) =>
      apiFetch<Expense>(`/expenses/${id}`, { method: "PATCH", body: data }),
    onSuccess: () => invalidateExpenseDependents(queryClient),
  })
}

function useDeleteExpense() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => apiFetch<null>(`/expenses/${id}`, { method: "DELETE" }),
    onSuccess: () => invalidateExpenseDependents(queryClient),
  })
}

export { useCreateExpense, useUpdateExpense, useDeleteExpense }
