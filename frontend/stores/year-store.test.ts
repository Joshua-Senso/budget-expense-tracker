import { beforeEach, expect, test } from "vitest"

import { getCurrentYear, useYearStore } from "@/stores/year-store"

beforeEach(() => {
  useYearStore.setState({ year: getCurrentYear() })
})

test("setYear replaces the selected year", () => {
  useYearStore.getState().setYear(2024)

  expect(useYearStore.getState().year).toBe(2024)
})

test("shiftYear moves forward", () => {
  useYearStore.getState().setYear(2025)
  useYearStore.getState().shiftYear(1)

  expect(useYearStore.getState().year).toBe(2026)
})

test("shiftYear moves backward", () => {
  useYearStore.getState().setYear(2025)
  useYearStore.getState().shiftYear(-1)

  expect(useYearStore.getState().year).toBe(2024)
})
