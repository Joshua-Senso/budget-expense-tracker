import { beforeEach, expect, test } from "vitest"

import {
  getCurrentMonth,
  toMonthKey,
  useMonthStore,
} from "@/stores/month-store"

beforeEach(() => {
  useMonthStore.setState(getCurrentMonth())
})

test("setMonth replaces the selected month", () => {
  useMonthStore.getState().setMonth({ year: 2026, month: 3 })

  expect(useMonthStore.getState()).toMatchObject({ year: 2026, month: 3 })
})

test("shiftMonth moves forward and across a year boundary", () => {
  useMonthStore.getState().setMonth({ year: 2025, month: 12 })
  useMonthStore.getState().shiftMonth(1)

  expect(useMonthStore.getState()).toMatchObject({ year: 2026, month: 1 })
})

test("shiftMonth moves backward and across a year boundary", () => {
  useMonthStore.getState().setMonth({ year: 2026, month: 1 })
  useMonthStore.getState().shiftMonth(-1)

  expect(useMonthStore.getState()).toMatchObject({ year: 2025, month: 12 })
})

test("toMonthKey pads the month to two digits", () => {
  expect(toMonthKey({ year: 2026, month: 3 })).toBe("2026-03")
  expect(toMonthKey({ year: 2026, month: 12 })).toBe("2026-12")
})
