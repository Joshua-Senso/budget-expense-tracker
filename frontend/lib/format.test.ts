import { afterEach, describe, expect, it, vi } from "vitest"

import { formatCurrency } from "./format"

describe("formatCurrency", () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("formats a valid ISO currency code", () => {
    expect(formatCurrency(85.5, "PHP")).toContain("85.50")
  })

  it("falls back to a plain string if Intl.NumberFormat throws", () => {
    vi.spyOn(Intl, "NumberFormat").mockImplementation(() => {
      throw new RangeError("Invalid currency code")
    })

    expect(formatCurrency(4.75, "PHP")).toBe("PHP 4.75")
  })
})
