"use client"

import { useState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { ApiError } from "@/lib/api-client"
import { formatExpenseDate } from "@/lib/format"

import { useImportExpenses } from "../api/mutations"
import {
  importFileSchema,
  type ImportConfirmationRequired,
  type ImportFileFormValues,
  type ImportRowError,
  type ImportSummary,
} from "../schemas"

type ImportErrorDisplay =
  | { kind: "message"; message: string }
  | { kind: "rows"; errors: ImportRowError[] }

const fallbackMessage = "Could not import this file. Please try again."

function getErrorDetail(err: ApiError) {
  return typeof err.body === "object" && err.body !== null && "detail" in err.body
    ? (err.body as { detail?: unknown }).detail
    : null
}

function isImportRowError(value: unknown): value is ImportRowError {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as { row?: unknown }).row === "number" &&
    Array.isArray((value as { messages?: unknown }).messages) &&
    (value as { messages: unknown[] }).messages.every((message) => typeof message === "string")
  )
}

function messageFromDetailItem(item: unknown): string {
  if (typeof item === "string") {
    return item
  }

  if (typeof item === "object" && item !== null && typeof (item as { msg?: unknown }).msg === "string") {
    return (item as { msg: string }).msg
  }

  return fallbackMessage
}

function getImportErrorDisplay(err: unknown): ImportErrorDisplay {
  if (err instanceof ApiError) {
    const detail = getErrorDetail(err)

    if (Array.isArray(detail) && detail.length > 0) {
      return detail.every(isImportRowError)
        ? { kind: "rows", errors: detail }
        : { kind: "message", message: detail.map(messageFromDetailItem).join(" ") }
    }

    if (typeof detail === "string") {
      return { kind: "message", message: detail }
    }
  }

  return { kind: "message", message: fallbackMessage }
}

function getRequiresConfirmation(err: unknown): ImportConfirmationRequired | null {
  if (!(err instanceof ApiError) || err.status !== 409) {
    return null
  }

  const detail = getErrorDetail(err)
  if (
    typeof detail === "object" &&
    detail !== null &&
    (detail as { requires_confirmation?: unknown }).requires_confirmation === true &&
    Array.isArray((detail as { deleted?: unknown }).deleted)
  ) {
    return detail as ImportConfirmationRequired
  }

  return null
}

interface ImportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  year: number
}

function ImportDialog({ open, onOpenChange, year }: ImportDialogProps) {
  const importExpenses = useImportExpenses()
  const [error, setError] = useState<ImportErrorDisplay | null>(null)
  const [summary, setSummary] = useState<ImportSummary | null>(null)
  const [pendingConfirmation, setPendingConfirmation] = useState<{
    file: File
    deletions: ImportConfirmationRequired["deleted"]
  } | null>(null)

  const form = useForm<ImportFileFormValues>({
    resolver: zodResolver(importFileSchema),
    defaultValues: { file: undefined },
  })

  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen) {
      setError(null)
      setSummary(null)
      setPendingConfirmation(null)
      form.reset({ file: undefined })
    }
    onOpenChange(nextOpen)
  }

  async function onSubmit(values: ImportFileFormValues) {
    setError(null)
    setSummary(null)

    try {
      const result = await importExpenses.mutateAsync({ year, file: values.file })
      setSummary(result)
      form.reset({ file: undefined })
    } catch (err) {
      const confirmation = getRequiresConfirmation(err)
      if (confirmation) {
        setPendingConfirmation({ file: values.file, deletions: confirmation.deleted })
        return
      }
      setError(getImportErrorDisplay(err))
    }
  }

  async function handleConfirmDeletions() {
    if (!pendingConfirmation) {
      return
    }

    setError(null)
    try {
      const result = await importExpenses.mutateAsync({
        year,
        file: pendingConfirmation.file,
        confirmDeletions: true,
      })
      setSummary(result)
      setPendingConfirmation(null)
      form.reset({ file: undefined })
    } catch (err) {
      setPendingConfirmation(null)
      setError(getImportErrorDisplay(err))
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Import expenses for {year}</DialogTitle>
          <DialogDescription>
            Upload an .xlsx or .xls file exported from this app. The sheet replaces the
            year&apos;s expenses entirely — rows you remove are deleted, and system columns
            (recurring/installment IDs) must stay as exported. Nothing is saved if any row
            fails validation.
          </DialogDescription>
        </DialogHeader>

        {pendingConfirmation ? (
          <>
            <p className="text-sm" role="alert">
              This import will delete {pendingConfirmation.deletions.length}{" "}
              {pendingConfirmation.deletions.length === 1 ? "expense" : "expenses"} not
              present in the sheet:
            </p>
            <ul className="max-h-48 list-disc space-y-1 overflow-y-auto pl-4 text-sm">
              {pendingConfirmation.deletions.map((deletion) => (
                <li key={deletion.row_id}>
                  {deletion.description} — {formatExpenseDate(deletion.spent_on)}
                </li>
              ))}
            </ul>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setPendingConfirmation(null)}
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant="destructive"
                disabled={importExpenses.isPending}
                onClick={handleConfirmDeletions}
              >
                {importExpenses.isPending ? (
                  <span className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                ) : (
                  "Confirm & import"
                )}
              </Button>
            </DialogFooter>
          </>
        ) : summary ? (
          <>
            <p className="text-sm" role="status">
              Import complete: {summary.inserted} added, {summary.updated} updated,{" "}
              {summary.deleted} deleted.
            </p>
            <DialogFooter>
              <Button type="button" onClick={() => handleOpenChange(false)}>
                Done
              </Button>
            </DialogFooter>
          </>
        ) : (
          <>
            <Form {...form}>
              <form id="import-form" onSubmit={form.handleSubmit(onSubmit)}>
                <FormField
                  control={form.control}
                  name="file"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>File</FormLabel>
                      <FormControl>
                        <Input
                          type="file"
                          accept=".xlsx,.xls"
                          name={field.name}
                          ref={field.ref}
                          onBlur={field.onBlur}
                          onChange={(event) => field.onChange(event.target.files?.[0])}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {error && (
                  <div className="mt-3 text-sm text-destructive" role="alert">
                    {error.kind === "message" ? (
                      <p>{error.message}</p>
                    ) : (
                      <ul className="list-disc space-y-1 pl-4">
                        {error.errors.map((rowError, index) => (
                          <li key={index}>
                            {rowError.row > 0 ? `Row ${rowError.row}: ` : ""}
                            {rowError.messages.join(", ")}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </form>
            </Form>

            <DialogFooter showCloseButton>
              <Button type="submit" form="import-form" disabled={importExpenses.isPending}>
                {importExpenses.isPending ? (
                  <span className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                ) : (
                  "Import"
                )}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}

export { ImportDialog }
