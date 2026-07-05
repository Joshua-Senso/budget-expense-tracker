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

import { useImportExpenses } from "../api/mutations"
import { importFileSchema, type ImportFileFormValues, type ImportRowError, type ImportSummary } from "../schemas"

type ImportErrorDisplay =
  | { kind: "message"; message: string }
  | { kind: "rows"; errors: ImportRowError[] }

function getErrorDetail(err: ApiError) {
  return typeof err.body === "object" && err.body !== null && "detail" in err.body
    ? (err.body as { detail?: unknown }).detail
    : null
}

function getImportErrorDisplay(err: unknown): ImportErrorDisplay {
  if (err instanceof ApiError) {
    const detail = getErrorDetail(err)

    if (err.status === 422 && Array.isArray(detail)) {
      return { kind: "rows", errors: detail as ImportRowError[] }
    }

    if (err.status === 400 && typeof detail === "string") {
      return { kind: "message", message: detail }
    }
  }

  return { kind: "message", message: "Could not import this file. Please try again." }
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

  const form = useForm<ImportFileFormValues>({
    resolver: zodResolver(importFileSchema),
    defaultValues: { file: undefined },
  })

  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen) {
      setError(null)
      setSummary(null)
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

        {summary ? (
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
