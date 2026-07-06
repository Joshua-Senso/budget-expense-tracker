"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { QueryClient } from "@tanstack/react-query"

import { apiFetch } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import { useWorkspaceStore } from "@/stores/workspace-store"

import type { Expense, ExpensePayload, InstallmentCreatePayload } from "../schemas"

function invalidateExpenseDependents(queryClient: QueryClient) {
  queryClient.invalidateQueries({ queryKey: queryKeys.expenses() })
  queryClient.invalidateQueries({ queryKey: queryKeys.dashboard() })
}

function useCreateExpense() {
  const queryClient = useQueryClient()
  const householdId = useWorkspaceStore((state) => state.activeWorkspaceId)

  return useMutation({
    mutationFn: (data: ExpensePayload) =>
      apiFetch<Expense>("/expenses", {
        method: "POST",
        body: { ...data, household_id: householdId },
      }),
    onSuccess: () => invalidateExpenseDependents(queryClient),
  })
}

function useCreateInstallmentExpense() {
  const queryClient = useQueryClient()
  const householdId = useWorkspaceStore((state) => state.activeWorkspaceId)

  return useMutation({
    mutationFn: (data: InstallmentCreatePayload) =>
      apiFetch<Expense[]>("/expenses/installments", {
        method: "POST",
        body: { ...data, household_id: householdId },
      }),
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
    mutationFn: ({ id, scope }: { id: string; scope?: "row" | "group" }) =>
      apiFetch<null>(`/expenses/${id}${scope ? `?scope=${scope}` : ""}`, {
        method: "DELETE",
      }),
    onSuccess: () => invalidateExpenseDependents(queryClient),
  })
}

export { useCreateExpense, useCreateInstallmentExpense, useUpdateExpense, useDeleteExpense }
