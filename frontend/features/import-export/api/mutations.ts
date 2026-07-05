"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { QueryClient } from "@tanstack/react-query"

import { apiFetch, apiFetchBlob } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"

import type { ImportSummary } from "../schemas"

function invalidateImportDependents(queryClient: QueryClient) {
  queryClient.invalidateQueries({ queryKey: queryKeys.expenses() })
  queryClient.invalidateQueries({ queryKey: queryKeys.dashboard() })
  queryClient.invalidateQueries({ queryKey: queryKeys.dashboardYearly() })
}

function useImportExpenses() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ year, file }: { year: number; file: File }) => {
      const formData = new FormData()
      formData.append("file", file)

      return apiFetch<ImportSummary>(`/import-export/import/${year}`, {
        method: "POST",
        body: formData,
      })
    },
    onSuccess: () => invalidateImportDependents(queryClient),
  })
}

function useExportExpenses() {
  return useMutation({
    mutationFn: ({ year }: { year: number }) =>
      apiFetchBlob(`/import-export/export/${year}`),
  })
}

export { useImportExpenses, useExportExpenses }
