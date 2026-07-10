import { renderHook } from "@testing-library/react"
import { beforeEach, expect, test } from "vitest"

import {
  useExpenseFilterStore,
  useResetExpenseFilterOnWorkspaceChange,
} from "@/features/expenses/store"
import { useWorkspaceStore } from "@/stores/workspace-store"

beforeEach(() => {
  useExpenseFilterStore.setState({ filter: { type: "all" } })
  useWorkspaceStore.setState({ activeWorkspaceId: null, activeWorkspaceScope: "personal" })
})

test("defaults to the all filter", () => {
  expect(useExpenseFilterStore.getState().filter).toEqual({ type: "all" })
})

test("setFilter switches to a group filter", () => {
  useExpenseFilterStore.getState().setFilter({ type: "card" })

  expect(useExpenseFilterStore.getState().filter).toEqual({ type: "card" })
})

test("setFilter switches to a category filter", () => {
  useExpenseFilterStore.getState().setFilter({
    type: "category",
    categoryId: "cat-1",
  })

  expect(useExpenseFilterStore.getState().filter).toEqual({
    type: "category",
    categoryId: "cat-1",
  })
})

test("setFilter replaces a category filter with a group filter", () => {
  useExpenseFilterStore.getState().setFilter({
    type: "category",
    categoryId: "cat-1",
  })
  useExpenseFilterStore.getState().setFilter({ type: "other" })

  expect(useExpenseFilterStore.getState().filter).toEqual({ type: "other" })
})

test("useResetExpenseFilterOnWorkspaceChange resets a category filter when the active workspace changes", () => {
  const { rerender } = renderHook(() => useResetExpenseFilterOnWorkspaceChange())

  useExpenseFilterStore.getState().setFilter({
    type: "category",
    categoryId: "cat-1",
  })
  expect(useExpenseFilterStore.getState().filter).toEqual({
    type: "category",
    categoryId: "cat-1",
  })

  useWorkspaceStore.getState().setActiveWorkspace({ id: "house-1" })
  rerender()

  expect(useExpenseFilterStore.getState().filter).toEqual({ type: "all" })
})

test("useResetExpenseFilterOnWorkspaceChange leaves the filter alone across an unrelated rerender", () => {
  const { rerender } = renderHook(() => useResetExpenseFilterOnWorkspaceChange())

  useExpenseFilterStore.getState().setFilter({ type: "card" })
  rerender()

  expect(useExpenseFilterStore.getState().filter).toEqual({ type: "card" })
})
