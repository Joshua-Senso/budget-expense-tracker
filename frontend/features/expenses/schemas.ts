import { z } from "zod"

const dateRegex = /^\d{4}-\d{2}-\d{2}$/

function isValidDate(value: string) {
  const date = new Date(`${value}T00:00:00Z`)

  return !Number.isNaN(date.getTime()) && date.toISOString().startsWith(value)
}

export const expenseSchema = z.object({
  description: z.string().trim().min(1, "Description is required"),
  amount: z
    .number({ error: "Amount is required" })
    .positive("Amount must be positive"),
  currency: z
    .string()
    .trim()
    .toUpperCase()
    .regex(/^[A-Z]{3}$/, "Use a 3-letter currency code"),
  spent_on: z
    .string()
    .regex(dateRegex, "Use YYYY-MM-DD")
    .refine(isValidDate, "Enter a valid date"),
  expense_group: z.enum(["card", "other"]),
  category_id: z.string().trim().min(1, "Category is required"),
})

export type ExpenseFormValues = z.infer<typeof expenseSchema>

export type ExpensePayload = Omit<ExpenseFormValues, "expense_group">

export type Expense = ExpensePayload & {
  id: string
  user_id: string
  created_at: string
  updated_at: string
}

export function toExpensePayload(values: ExpenseFormValues): ExpensePayload {
  return {
    description: values.description,
    amount: values.amount,
    currency: values.currency,
    spent_on: values.spent_on,
    category_id: values.category_id,
  }
}
