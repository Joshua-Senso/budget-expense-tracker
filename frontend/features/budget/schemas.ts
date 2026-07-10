import { z } from "zod"

export const monthlySettingSchema = z.object({
  monthly_net_salary: z
    .number({ error: "Salary is required" })
    .min(0, "Salary must be zero or greater")
    .max(9_999_999_999.99, "Salary is too large")
    .refine((value) => Number(value.toFixed(2)) === value, {
      message: "Use no more than 2 decimal places",
    }),
})

export type MonthlySettingFormValues = z.infer<typeof monthlySettingSchema>

export type MonthlySetting = {
  id: string
  user_id: string
  month_key: string
  monthly_net_salary: string
  base_currency: string | null
  created_at: string
  updated_at: string
}
