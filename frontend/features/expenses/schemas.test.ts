import { describe, expect, it } from "vitest"

import { createExpenseSchema, expenseSchema } from "./schemas"

const baseExpense = {
  description: "Lunch",
  amount: 150,
  currency: "PHP",
  spent_on: "2026-07-01",
  expense_group: "other" as const,
  category_id: "cat-1",
}

function baseExpenseWithoutSpentOn() {
  const rest: Partial<typeof baseExpense> = { ...baseExpense }
  delete rest.spent_on
  return rest
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

describe("createExpenseSchema", () => {
  it("accepts a one-time expense with a spent_on date", () => {
    expect(() =>
      createExpenseSchema.parse({ ...baseExpense, expense_type: "one_time" }),
    ).not.toThrow()
  })

  it("rejects a one-time expense missing spent_on", () => {
    const rest = baseExpenseWithoutSpentOn()
    expect(() =>
      createExpenseSchema.parse({ ...rest, expense_type: "one_time" }),
    ).toThrow()
  })

  it("accepts an installment expense with a valid installment_total", () => {
    expect(() =>
      createExpenseSchema.parse({
        ...baseExpense,
        expense_type: "installment",
        installment_total: 6,
      }),
    ).not.toThrow()
  })

  it.each([1, 61, 2.5])(
    "rejects an installment expense with an out-of-range installment_total %s",
    (installment_total) => {
      expect(() =>
        createExpenseSchema.parse({
          ...baseExpense,
          expense_type: "installment",
          installment_total,
        }),
      ).toThrow()
    },
  )

  it("accepts a recurring expense with only a start_on date", () => {
    const rest = baseExpenseWithoutSpentOn()
    expect(() =>
      createExpenseSchema.parse({
        ...rest,
        expense_type: "recurring",
        start_on: "2026-07-01",
      }),
    ).not.toThrow()
  })

  it("rejects a recurring expense missing start_on", () => {
    const rest = baseExpenseWithoutSpentOn()
    expect(() =>
      createExpenseSchema.parse({ ...rest, expense_type: "recurring" }),
    ).toThrow()
  })

  it("rejects a recurring expense whose end_on is before start_on", () => {
    const rest = baseExpenseWithoutSpentOn()
    expect(() =>
      createExpenseSchema.parse({
        ...rest,
        expense_type: "recurring",
        start_on: "2026-07-01",
        end_on: "2026-06-01",
      }),
    ).toThrow("End date must be on or after the start date")
  })
})
