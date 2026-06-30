import { z } from "zod"

const hexColorRegex = /^#[0-9A-Fa-f]{6}$/

export const categorySchema = z.object({
  name: z.string().min(1, "Name is required"),
  color: z.string().regex(hexColorRegex, "Must be a 6-digit hex color (e.g. #FF0000)"),
  expense_group: z.enum(["card", "other"]),
})

export type CategoryFormValues = z.infer<typeof categorySchema>

export type Category = {
  id: string
  user_id: string
  name: string
  color: string
  expense_group: "card" | "other"
  created_at: string
  updated_at: string
}
