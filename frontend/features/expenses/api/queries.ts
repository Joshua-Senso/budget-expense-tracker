"use client"

import { useQuery } from "@tanstack/react-query"

import { apiFetch, buildSearchParams } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import { toMonthKey } from "@/stores/month-store"
import type { SelectedMonth } from "@/stores/month-store"
import { useWorkspaceStore } from "@/stores/workspace-store"

import type { Expense } from "../schemas"

function useExpenses(month: SelectedMonth) {
  const householdId = useWorkspaceStore((state) => state.activeWorkspaceId)

  return useQuery({
    queryKey: queryKeys.expenses(toMonthKey(month), householdId),
    queryFn: () =>
      apiFetch<Expense[]>(
        `/expenses${buildSearchParams({
          year: month.year,
          month: month.month,
          household_id: householdId,
        })}`,
      ),
  })
}

export { useExpenses }
