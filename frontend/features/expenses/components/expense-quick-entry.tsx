"use client"

import { useState } from "react"
import { PlusIcon } from "lucide-react"

import { Button } from "@/components/ui/button"

import { ExpenseFormDialog } from "./expense-form-dialog"

function ExpenseQuickEntry() {
  const [open, setOpen] = useState(false)

  return (
    <>
      <div className="rounded-3xl border bg-card p-5 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground uppercase">
              Expense entry
            </p>
            <h2 className="mt-1 text-xl font-semibold tracking-tight">
              Log a one-time expense
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Add the date, amount, type, and category in one short form.
            </p>
          </div>
          <Button onClick={() => setOpen(true)} className="gap-1.5 sm:self-end">
            <PlusIcon />
            Add expense
          </Button>
        </div>
      </div>

      <ExpenseFormDialog open={open} onOpenChange={setOpen} />
    </>
  )
}

export { ExpenseQuickEntry }
