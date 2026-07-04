"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"

import { apiFetch } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import { toMonthKey } from "@/stores/month-store"
import type { SelectedMonth } from "@/stores/month-store"

import type { MonthlySetting, MonthlySettingFormValues } from "../schemas"

function useUpsertMonthlySetting(month: SelectedMonth) {
  const queryClient = useQueryClient()
  const monthKey = toMonthKey(month)

  return useMutation({
    mutationFn: (data: MonthlySettingFormValues) =>
      apiFetch<MonthlySetting>(`/budget/settings/${monthKey}`, {
        method: "PUT",
        body: data,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.budgetSettings(monthKey),
      })
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard(monthKey) })
    },
  })
}

export { useUpsertMonthlySetting }
