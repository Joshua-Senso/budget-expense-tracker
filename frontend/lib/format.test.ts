import { afterEach, describe, expect, it, vi } from "vitest"

import { formatConvertedAmount, formatCurrency } from "./format"

describe("formatCurrency", () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("formats a valid ISO currency code", () => {
    expect(formatCurrency(85.5, "PHP")).toContain("85.50")
  })

  it("shows the currency code, not an ambiguous symbol", () => {
    // USD, CAD, HKD, SGD, AUD, NZD all render "$" as a symbol -- the code
    // is the only unambiguous way to tell them apart at a glance.
    expect(formatCurrency(100, "USD")).toContain("USD")
    expect(formatCurrency(100, "USD")).not.toContain("$")
  })

  it("respects each currency's decimal digits (e.g. JPY has none)", () => {
    expect(formatCurrency(1234.5, "JPY")).toContain("1,235")
    expect(formatCurrency(1234.5, "JPY")).not.toContain(".")
  })

  it("falls back to a plain string if Intl.NumberFormat throws", () => {
    vi.spyOn(Intl, "NumberFormat").mockImplementation(() => {
      throw new RangeError("Invalid currency code")
    })

    expect(formatCurrency(4.75, "PHP")).toBe("PHP 4.75")
  })
})

describe("formatConvertedAmount", () => {
  it("returns no conversion when the amount is already in the base currency", () => {
    const result = formatConvertedAmount(150, "PHP", 150, "PHP")

    expect(result.primary).toContain("150.00")
    expect(result.converted).toBeNull()
  })

  it("includes the base-currency conversion when currencies differ", () => {
    const result = formatConvertedAmount(100, "USD", 5600, "PHP")

    expect(result.primary).toContain("USD")
    expect(result.primary).toContain("100.00")
    expect(result.converted).toContain("PHP")
    expect(result.converted).toContain("5,600.00")
  })
})
