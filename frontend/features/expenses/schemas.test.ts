import { describe, expect, it } from "vitest"

import { expenseSchema } from "./schemas"

const baseExpense = {
  description: "Lunch",
  amount: 150,
  currency: "PHP",
  spent_on: "2026-07-01",
  expense_group: "other" as const,
  category_id: "cat-1",
}

describe("expenseSchema", () => {
  it.each([19.99, 0.07, 1.1, 8.2, 0.29, 4.9])(
    "accepts valid 2-decimal amount %s",
    (amount) => {
      expect(() => expenseSchema.parse({ ...baseExpense, amount })).not.toThrow()
    },
  )

  it("rejects amounts with more than 2 decimal places", () => {
    expect(() =>
      expenseSchema.parse({ ...baseExpense, amount: 150.999 }),
    ).toThrow("Use no more than 2 decimal places")
  })
})
