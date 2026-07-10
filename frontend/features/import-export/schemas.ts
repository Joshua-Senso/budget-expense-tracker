import { z } from "zod"

export const importFileSchema = z.object({
  file: z
    .instanceof(File, { error: "Choose a file to import" })
    .refine((file) => /\.(xlsx|xls)$/i.test(file.name), {
      message: "File must be .xlsx or .xls",
    }),
})

export type ImportFileFormValues = z.infer<typeof importFileSchema>

export type ImportSummary = {
  inserted: number
  updated: number
  deleted: number
}

export type ImportRowError = {
  row: number
  messages: string[]
}

export type PendingDeletion = {
  row_id: string
  description: string
  spent_on: string
}

export type ImportConfirmationRequired = {
  requires_confirmation: true
  deleted: PendingDeletion[]
}
