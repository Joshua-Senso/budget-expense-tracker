"use client"

import { useQuery } from "@tanstack/react-query"

import { apiFetch, buildSearchParams } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import { useWorkspaceStore } from "@/stores/workspace-store"

import type { Category } from "../schemas"

function useCategories() {
  const householdId = useWorkspaceStore((state) => state.activeWorkspaceId)

  return useQuery({
    queryKey: queryKeys.categories(householdId),
    queryFn: () =>
      apiFetch<Category[]>(
        `/categories${buildSearchParams({ household_id: householdId })}`,
      ),
  })
}

export { useCategories }
