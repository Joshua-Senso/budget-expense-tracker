"use client"

import { useQuery } from "@tanstack/react-query"

import { apiFetch } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import { toMonthKey } from "@/stores/month-store"
import type { SelectedMonth } from "@/stores/month-store"

import type { DashboardSummaryData, YearlyOverviewData } from "../schemas"

function useDashboardSummary(month: SelectedMonth) {
  const monthKey = toMonthKey(month)

  return useQuery({
    queryKey: queryKeys.dashboard(monthKey),
    queryFn: () =>
      apiFetch<DashboardSummaryData>(`/dashboard/summary/${monthKey}`),
  })
}

function useYearlyOverview(year: number) {
  return useQuery({
    queryKey: queryKeys.dashboardYearly(year),
    queryFn: () => apiFetch<YearlyOverviewData>(`/dashboard/yearly/${year}`),
  })
}

export { useDashboardSummary, useYearlyOverview }
