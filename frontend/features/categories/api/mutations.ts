"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { QueryClient } from "@tanstack/react-query"

import { apiFetch } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"

import type { Category, CategoryFormValues } from "../schemas"

function invalidateCategories(queryClient: QueryClient) {
  queryClient.invalidateQueries({ queryKey: queryKeys.categories() })
}

function useCreateCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CategoryFormValues) =>
      apiFetch<Category>("/categories", { method: "POST", body: data }),
    onSuccess: () => invalidateCategories(queryClient),
  })
}

function useUpdateCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string
      data: Partial<CategoryFormValues>
    }) =>
      apiFetch<Category>(`/categories/${id}`, { method: "PATCH", body: data }),
    onSuccess: () => invalidateCategories(queryClient),
  })
}

function useDeleteCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<null>(`/categories/${id}`, { method: "DELETE" }),
    onSuccess: () => invalidateCategories(queryClient),
  })
}

export { useCreateCategory, useUpdateCategory, useDeleteCategory }
