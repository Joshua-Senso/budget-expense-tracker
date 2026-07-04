"use client"

import { useQuery } from "@tanstack/react-query"

import { ApiError, apiFetch } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import { toMonthKey } from "@/stores/month-store"
import type { SelectedMonth } from "@/stores/month-store"

import type { MonthlySetting } from "../schemas"

async function fetchMonthlySetting(
  monthKey: string
): Promise<MonthlySetting | null> {
  try {
    return await apiFetch<MonthlySetting>(`/budget/settings/${monthKey}`)
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      return null
    }
    throw err
  }
}

function useMonthlySetting(month: SelectedMonth) {
  const monthKey = toMonthKey(month)

  return useQuery({
    queryKey: queryKeys.budgetSettings(monthKey),
    queryFn: () => fetchMonthlySetting(monthKey),
  })
}

export { useMonthlySetting }
