"use client"

import { useQuery } from "@tanstack/react-query"

import { apiFetch } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import { toMonthKey } from "@/stores/month-store"
import type { SelectedMonth } from "@/stores/month-store"

import type { ProjectedExpense } from "../schemas"

function useRecurringProjection(month: SelectedMonth) {
  const monthKey = toMonthKey(month)

  return useQuery({
    queryKey: queryKeys.recurringProjection(monthKey),
    queryFn: () => apiFetch<ProjectedExpense[]>(`/recurring/projection/${monthKey}`),
  })
}

export { useRecurringProjection }
