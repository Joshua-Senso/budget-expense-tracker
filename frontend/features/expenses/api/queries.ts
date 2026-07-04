"use client"

import { useQuery } from "@tanstack/react-query"

import { apiFetch } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"

import type { Expense } from "../schemas"

function useExpenses() {
  return useQuery({
    queryKey: queryKeys.expenses(),
    queryFn: () => apiFetch<Expense[]>("/expenses"),
  })
}

export { useExpenses }
