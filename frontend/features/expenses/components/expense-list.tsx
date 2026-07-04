"use client"

import { useMemo, useState } from "react"
import { PencilIcon, Trash2Icon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { CategoryColor, useCategories } from "@/features/categories"
import { ApiError } from "@/lib/api-client"
import {
  formatCurrency,
  formatExpenseDate,
  formatMonthLabel,
} from "@/lib/format"
import { useMonthStore } from "@/stores/month-store"

import { useDeleteExpense } from "../api/mutations"
import { useExpenses } from "../api/queries"
import { ExpenseFormDialog } from "./expense-form-dialog"
import type { Expense } from "../schemas"

function getDeleteErrorMessage(err: unknown) {
  if (err instanceof ApiError && err.status === 404) {
    return "This expense no longer exists. Refresh the page and try again."
  }

  return "Could not delete expense. Please try again."
}

function ExpenseList() {
  const selectedMonth = useMonthStore(({ year, month }) => ({ year, month }))
  const {
    data: expenses,
    isLoading: expensesLoading,
    isError: expensesError,
  } = useExpenses(selectedMonth)
  const monthExpenses = expenses ?? []
  const { data: categories, isError: categoriesError } = useCategories()
  const deleteExpense = useDeleteExpense()

  const [editTarget, setEditTarget] = useState<Expense | undefined>(undefined)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleteErrors, setDeleteErrors] = useState<Record<string, string>>({})
  const [pendingDeleteIds, setPendingDeleteIds] = useState<Set<string>>(
    new Set()
  )

  const categoryById = useMemo(
    () =>
      new Map((categories ?? []).map((category) => [category.id, category])),
    [categories]
  )

  function openEdit(expense: Expense) {
    setEditTarget(expense)
    setDialogOpen(true)
  }

  function handleDialogOpenChange(open: boolean) {
    setDialogOpen(open)
    if (!open) {
      setEditTarget(undefined)
    }
  }

  async function handleDelete(expense: Expense) {
    setDeleteErrors((prev) => {
      const next = { ...prev }
      delete next[expense.id]
      return next
    })
    setPendingDeleteIds((prev) => new Set(prev).add(expense.id))
    try {
      await deleteExpense.mutateAsync(expense.id)
    } catch (err) {
      setDeleteErrors((prev) => ({
        ...prev,
        [expense.id]: getDeleteErrorMessage(err),
      }))
    } finally {
      setPendingDeleteIds((prev) => {
        const next = new Set(prev)
        next.delete(expense.id)
        return next
      })
    }
  }

  return (
    <section className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold tracking-tight">Expenses</h2>

      {expensesLoading && (
        <p className="text-sm text-muted-foreground">Loading…</p>
      )}

      {expensesError && (
        <p className="text-sm text-destructive" role="alert">
          Failed to load expenses.
        </p>
      )}

      {categoriesError && !expensesError && (
        <p className="text-sm text-destructive" role="alert">
          Failed to load categories. Category names and colors may be
          unavailable.
        </p>
      )}

      {!expensesLoading && !expensesError && monthExpenses.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No expenses recorded for{" "}
          {formatMonthLabel(selectedMonth.year, selectedMonth.month)}.
        </p>
      )}

      {!expensesLoading && !expensesError && monthExpenses.length > 0 && (
        <ul className="flex flex-col gap-2">
          {monthExpenses.map((expense) => {
            const category = categoryById.get(expense.category_id)

            return (
              <li key={expense.id} className="flex flex-col gap-1">
                <div className="flex items-center gap-3 rounded-2xl border bg-card px-4 py-3">
                  <CategoryColor
                    color={category?.color ?? "#9ca3af"}
                    className="size-5"
                  />

                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="truncate text-sm font-medium">
                        {expense.description}
                      </span>
                      <span className="shrink-0 text-xs text-muted-foreground">
                        {category?.name ?? "Uncategorized"}
                      </span>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {formatExpenseDate(expense.spent_on)}
                    </span>
                  </div>

                  <span className="shrink-0 text-sm font-semibold">
                    {formatCurrency(expense.amount, expense.currency)}
                  </span>

                  <div className="flex shrink-0 items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      aria-label={`Edit ${expense.description}`}
                      onClick={() => openEdit(expense)}
                    >
                      <PencilIcon />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      aria-label={`Delete ${expense.description}`}
                      onClick={() => handleDelete(expense)}
                      disabled={pendingDeleteIds.has(expense.id)}
                      className="text-destructive hover:text-destructive"
                    >
                      <Trash2Icon />
                    </Button>
                  </div>
                </div>

                {deleteErrors[expense.id] && (
                  <p className="px-4 text-xs text-destructive" role="alert">
                    {deleteErrors[expense.id]}
                  </p>
                )}
              </li>
            )
          })}
        </ul>
      )}

      <ExpenseFormDialog
        open={dialogOpen}
        onOpenChange={handleDialogOpenChange}
        expense={editTarget}
      />
    </section>
  )
}

export { ExpenseList }
