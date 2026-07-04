import { beforeEach, expect, test } from "vitest"

import { useExpenseFilterStore } from "@/features/expenses/store"

beforeEach(() => {
  useExpenseFilterStore.setState({ filter: { type: "all" } })
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
