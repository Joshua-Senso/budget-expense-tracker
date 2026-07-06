"use client"

import { useQuery } from "@tanstack/react-query"

import { apiFetch, buildSearchParams } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import { toMonthKey } from "@/stores/month-store"
import type { SelectedMonth } from "@/stores/month-store"
import { useWorkspaceStore } from "@/stores/workspace-store"

import type { DashboardSummaryData, YearlyOverviewData } from "../schemas"

function useDashboardSummary(month: SelectedMonth) {
  const householdId = useWorkspaceStore((state) => state.activeWorkspaceId)
  const monthKey = toMonthKey(month)

  return useQuery({
    queryKey: queryKeys.dashboard(monthKey, householdId),
    queryFn: () =>
      apiFetch<DashboardSummaryData>(
        `/dashboard/summary/${monthKey}${buildSearchParams({ household_id: householdId })}`,
      ),
  })
}

function useYearlyOverview(year: number) {
  const householdId = useWorkspaceStore((state) => state.activeWorkspaceId)

  return useQuery({
    queryKey: queryKeys.dashboardYearly(year, householdId),
    queryFn: () =>
      apiFetch<YearlyOverviewData>(
        `/dashboard/yearly/${year}${buildSearchParams({ household_id: householdId })}`,
      ),
  })
}

export { useDashboardSummary, useYearlyOverview }
