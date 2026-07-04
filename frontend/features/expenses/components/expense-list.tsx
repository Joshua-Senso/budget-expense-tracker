"use client"

import { useMemo, useState } from "react"
import { ChevronLeftIcon, ChevronRightIcon, PencilIcon, Trash2Icon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { CategoryColor, useCategories } from "@/features/categories"
import { ApiError } from "@/lib/api-client"
import { formatCurrency, formatExpenseDate, formatMonthLabel } from "@/lib/format"

import { useDeleteExpense } from "../api/mutations"
import { useExpenses } from "../api/queries"
import { ExpenseFormDialog } from "./expense-form-dialog"
import type { Expense } from "../schemas"

type MonthValue = { year: number; month: number }

function getCurrentMonth(): MonthValue {
  const now = new Date()

  return { year: now.getFullYear(), month: now.getMonth() + 1 }
}

function shiftMonth({ year, month }: MonthValue, delta: number): MonthValue {
  const date = new Date(Date.UTC(year, month - 1 + delta, 1))

  return { year: date.getUTCFullYear(), month: date.getUTCMonth() + 1 }
}

function toMonthKey({ year, month }: MonthValue): string {
  return `${year}-${String(month).padStart(2, "0")}`
}

function getDeleteErrorMessage(err: unknown) {
  if (err instanceof ApiError && err.status === 404) {
    return "This expense no longer exists. Refresh the page and try again."
  }

  return "Could not delete expense. Please try again."
}

function ExpenseList() {
  const [selectedMonth, setSelectedMonth] = useState<MonthValue>(getCurrentMonth)
  const { data: expenses, isLoading: expensesLoading, isError: expensesError } = useExpenses()
  const { data: categories, isError: categoriesError } = useCategories()
  const deleteExpense = useDeleteExpense()

  const [editTargetId, setEditTargetId] = useState<string | undefined>(undefined)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleteErrors, setDeleteErrors] = useState<Record<string, string>>({})
  const [pendingDeleteIds, setPendingDeleteIds] = useState<Set<string>>(new Set())

  const categoryById = useMemo(
    () => new Map((categories ?? []).map((category) => [category.id, category])),
    [categories],
  )

  const monthKey = toMonthKey(selectedMonth)
  const monthExpenses = useMemo(
    () => (expenses ?? []).filter((expense) => expense.spent_on.startsWith(monthKey)),
    [expenses, monthKey],
  )

  const editTarget = monthExpenses.find((expense) => expense.id === editTargetId)

  function openEdit(expense: Expense) {
    setEditTargetId(expense.id)
    setDialogOpen(true)
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
      setDeleteErrors((prev) => ({ ...prev, [expense.id]: getDeleteErrorMessage(err) }))
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
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold tracking-tight">
          {formatMonthLabel(selectedMonth.year, selectedMonth.month)}
        </h2>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Previous month"
            onClick={() => setSelectedMonth((month) => shiftMonth(month, -1))}
          >
            <ChevronLeftIcon />
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Next month"
            onClick={() => setSelectedMonth((month) => shiftMonth(month, 1))}
          >
            <ChevronRightIcon />
          </Button>
        </div>
      </div>

      {expensesLoading && <p className="text-sm text-muted-foreground">Loading…</p>}

      {expensesError && (
        <p className="text-sm text-destructive" role="alert">
          Failed to load expenses.
        </p>
      )}

      {categoriesError && !expensesError && (
        <p className="text-sm text-destructive" role="alert">
          Failed to load categories. Category names and colors may be unavailable.
        </p>
      )}

      {!expensesLoading && !expensesError && monthExpenses.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No expenses recorded for {formatMonthLabel(selectedMonth.year, selectedMonth.month)}.
        </p>
      )}

      {!expensesLoading && !expensesError && monthExpenses.length > 0 && (
        <ul className="flex flex-col gap-2">
          {monthExpenses.map((expense) => {
            const category = categoryById.get(expense.category_id)

            return (
              <li key={expense.id} className="flex flex-col gap-1">
                <div className="flex items-center gap-3 rounded-2xl border bg-card px-4 py-3">
                  <CategoryColor color={category?.color ?? "#9ca3af"} className="size-5" />

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

      <ExpenseFormDialog open={dialogOpen} onOpenChange={setDialogOpen} expense={editTarget} />
    </section>
  )
}

export { ExpenseList }
