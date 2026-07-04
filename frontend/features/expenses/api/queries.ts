"use client"

import { useQuery } from "@tanstack/react-query"

import { apiFetch } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"

import type { Expense } from "../schemas"

interface ExpenseMonth {
  year: number
  month: number
}

function toMonthKey({ year, month }: ExpenseMonth): string {
  return `${year}-${String(month).padStart(2, "0")}`
}

function useExpenses(month: ExpenseMonth) {
  return useQuery({
    queryKey: queryKeys.expenses(toMonthKey(month)),
    queryFn: () =>
      apiFetch<Expense[]>(`/expenses?year=${month.year}&month=${month.month}`),
  })
}

export { useExpenses }
export type { ExpenseMonth }
