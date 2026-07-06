"use client"

import { useQuery } from "@tanstack/react-query"

import { apiFetch, buildSearchParams } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import { toMonthKey } from "@/stores/month-store"
import type { SelectedMonth } from "@/stores/month-store"
import { useWorkspaceStore } from "@/stores/workspace-store"

import type { ProjectedExpense } from "../schemas"

function useRecurringProjection(month: SelectedMonth) {
  const householdId = useWorkspaceStore((state) => state.activeWorkspaceId)
  const monthKey = toMonthKey(month)

  return useQuery({
    queryKey: queryKeys.recurringProjection(monthKey, householdId),
    queryFn: () =>
      apiFetch<ProjectedExpense[]>(
        `/recurring/projection/${monthKey}${buildSearchParams({ household_id: householdId })}`,
      ),
  })
}

export { useRecurringProjection }
