import { z } from "zod"

import { SUPPORTED_CURRENCIES } from "@/features/currency"

const dateRegex = /^\d{4}-\d{2}-\d{2}$/
const maxAmount = 9_999_999_999.99

function isValidDate(value: string) {
  const date = new Date(`${value}T00:00:00Z`)

  return !Number.isNaN(date.getTime()) && date.toISOString().startsWith(value)
}

const amountSchema = z
  .number({ error: "Amount is required" })
  .positive("Amount must be positive")
  .max(maxAmount, "Amount is too large")
  .refine((value) => Number(value.toFixed(2)) === value, {
    message: "Use no more than 2 decimal places",
  })

const currencySchema = z
  .string()
  .trim()
  .toUpperCase()
  .refine((value) => (SUPPORTED_CURRENCIES as readonly string[]).includes(value), {
    message: "Choose a supported currency",
  })

const isoDateSchema = z
  .string()
  .regex(dateRegex, "Use YYYY-MM-DD")
  .refine(isValidDate, "Enter a valid date")

function isValidIsoDate(value: string | undefined): value is string {
  return value != null && isoDateSchema.safeParse(value).success
}

export const expenseSchema = z.object({
  description: z.string().trim().min(1, "Description is required"),
  amount: amountSchema,
  currency: currencySchema,
  spent_on: isoDateSchema,
  expense_group: z.enum(["card", "other"]),
  category_id: z.string().trim().min(1, "Category is required"),
})

export type ExpenseFormValues = z.infer<typeof expenseSchema>

export type ExpensePayload = Omit<ExpenseFormValues, "expense_group">

export type Expense = Omit<ExpensePayload, "amount"> & {
  id: string
  user_id: string
  amount: string
  base_amount: string
  exchange_rate: string
  installment_group_id: string | null
  installment_index: number | null
  installment_total: number | null
  original_description: string | null
  recurring_expense_id: string | null
  created_at: string
  updated_at: string
  isProjected?: boolean
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

export const expenseTypeSchema = z.enum(["one_time", "installment", "recurring"])

export type ExpenseType = z.infer<typeof expenseTypeSchema>

export const createExpenseSchema = z
  .object({
    expense_type: expenseTypeSchema,
    description: z.string().trim().min(1, "Description is required"),
    amount: amountSchema,
    currency: currencySchema,
    expense_group: z.enum(["card", "other"]),
    category_id: z.string().trim().min(1, "Category is required"),
    spent_on: z.string().optional(),
    installment_total: z.number().optional(),
    start_on: z.string().optional(),
    end_on: z.string().optional(),
  })
  .superRefine((values, ctx) => {
    if (values.expense_type !== "recurring" && !isValidIsoDate(values.spent_on)) {
      ctx.addIssue({ code: "custom", path: ["spent_on"], message: "Enter a valid date" })
    }

    if (values.expense_type === "installment") {
      if (
        values.installment_total == null ||
        !Number.isInteger(values.installment_total) ||
        values.installment_total < 2 ||
        values.installment_total > 60
      ) {
        ctx.addIssue({
          code: "custom",
          path: ["installment_total"],
          message: "Choose between 2 and 60 installments",
        })
      }
    }

    if (values.expense_type === "recurring") {
      if (!isValidIsoDate(values.start_on)) {
        ctx.addIssue({ code: "custom", path: ["start_on"], message: "Enter a valid date" })
      }
      if (values.end_on) {
        if (!isValidIsoDate(values.end_on)) {
          ctx.addIssue({ code: "custom", path: ["end_on"], message: "Enter a valid date" })
        } else if (values.start_on && values.end_on < values.start_on) {
          ctx.addIssue({
            code: "custom",
            path: ["end_on"],
            message: "End date must be on or after the start date",
          })
        }
      }
    }
  })

export type CreateExpenseFormValues = z.infer<typeof createExpenseSchema>

export type InstallmentCreatePayload = ExpensePayload & { installment_total: number }
