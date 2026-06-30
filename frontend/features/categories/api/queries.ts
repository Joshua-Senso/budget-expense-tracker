"use client"

import { useQuery } from "@tanstack/react-query"

import { apiFetch } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"

import type { Category } from "../schemas"

function useCategories() {
  return useQuery({
    queryKey: queryKeys.categories(),
    queryFn: () => apiFetch<Category[]>("/categories"),
  })
}

export { useCategories }
