import { expect, test } from "vitest"

import { queryKeys } from "./query-keys"

test("workspace-scoped keys default to a distinct 'personal' segment", () => {
  expect(queryKeys.categories(null)).toEqual([
    "expense-tracker",
    "categories",
    "personal",
  ])
  expect(queryKeys.categories("house-1")).toEqual([
    "expense-tracker",
    "categories",
    "house-1",
  ])
})

test("omitting the household argument yields a prefix of every workspace variant", () => {
  const broad = queryKeys.expenses("2026-07")
  const personal = queryKeys.expenses("2026-07", null)
  const household = queryKeys.expenses("2026-07", "house-1")

  expect(personal.slice(0, broad.length)).toEqual(broad)
  expect(household.slice(0, broad.length)).toEqual(broad)
})

test("dashboard keeps the month/year before the workspace segment so month-only invalidation still matches every workspace", () => {
  expect(queryKeys.dashboard("2026-07")).toEqual([
    "expense-tracker",
    "dashboard",
    "2026-07",
  ])
  expect(queryKeys.dashboard("2026-07", "house-1")).toEqual([
    "expense-tracker",
    "dashboard",
    "2026-07",
    "house-1",
  ])
  expect(queryKeys.dashboardYearly(2026, null)).toEqual([
    "expense-tracker",
    "dashboard-yearly",
    2026,
    "personal",
  ])
})
