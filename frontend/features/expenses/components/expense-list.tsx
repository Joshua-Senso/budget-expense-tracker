"use client"

import { useMemo, useState } from "react"
import { PencilIcon, Trash2Icon } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { CategoryColor, useCategories } from "@/features/categories"
import type { Category } from "@/features/categories"
import { useDashboardSummary } from "@/features/dashboard"
import { useRecurringProjection } from "@/features/recurring"
import {
  formatConvertedAmount,
  formatCurrency,
  formatExpenseDate,
  formatMonthLabel,
} from "@/lib/format"
import { cn } from "@/lib/utils"
import { useMonthStore } from "@/stores/month-store"

import { useDeleteExpense } from "../api/mutations"
import { useExpenses } from "../api/queries"
import { useExpenseFilterStore } from "../store"
import { ExpenseActionDialog, getDeleteErrorMessage } from "./expense-action-dialog"
import { ExpenseFilterBar } from "./expense-filter-bar"
import { ExpenseFormDialog } from "./expense-form-dialog"
import type { Expense } from "../schemas"
import type { ExpenseFilter } from "../store"

function mergeProjectedExpenses(
  persisted: Expense[],
  projected: ReturnType<typeof useRecurringProjection>["data"],
): Expense[] {
  const persistedKeys = new Set(
    persisted
      .filter((expense) => expense.recurring_expense_id)
      .map((expense) => `${expense.recurring_expense_id}:${expense.spent_on}`),
  )

  const projectedOnly: Expense[] = (projected ?? [])
    .filter((p) => !persistedKeys.has(`${p.recurring_expense_id}:${p.spent_on}`))
    .map((p) => ({
      id: `${p.recurring_expense_id}:${p.spent_on}`,
      description: p.description,
      amount: p.amount,
      currency: p.currency,
      // A projected occurrence isn't a persisted row yet, so it has no real
      // conversion computed for it (project_month doesn't resolve one) --
      // default to "unconverted" rather than fabricate one.
      base_amount: p.amount,
      exchange_rate: "1",
      spent_on: p.spent_on,
      category_id: p.category_id,
      user_id: "",
      installment_group_id: null,
      installment_index: null,
      installment_total: null,
      original_description: null,
      recurring_expense_id: p.recurring_expense_id,
      created_at: "",
      updated_at: "",
      isProjected: true,
    }))

  return [...persisted, ...projectedOnly].sort((a, b) =>
    a.spent_on < b.spent_on ? 1 : a.spent_on > b.spent_on ? -1 : 0,
  )
}

function matchesFilter(
  filter: ExpenseFilter,
  expense: Expense,
  category: Category | undefined
) {
  switch (filter.type) {
    case "all":
      return true
    case "card":
    case "other":
      return category?.expense_group === filter.type
    case "category":
      return expense.category_id === filter.categoryId
  }
}

function getFilterLabel(
  filter: ExpenseFilter,
  categoryById: Map<string, Category>
) {
  switch (filter.type) {
    case "all":
      return null
    case "card":
      return "card"
    case "other":
      return "other"
    case "category":
      return categoryById.get(filter.categoryId)?.name ?? "this category"
  }
}

function ExpenseAmount({
  expense,
  baseCurrency,
}: {
  expense: Expense
  baseCurrency: string
}) {
  const { primary, converted } = formatConvertedAmount(
    expense.amount,
    expense.currency,
    expense.base_amount,
    baseCurrency
  )

  return (
    <span className="flex shrink-0 flex-col items-end">
      <span className="text-sm font-semibold">{primary}</span>
      {converted && (
        <span className="text-xs text-muted-foreground">≈ {converted}</span>
      )}
    </span>
  )
}

function ExpenseList() {
  const year = useMonthStore((state) => state.year)
  const month = useMonthStore((state) => state.month)
  const {
    data: expenses,
    isLoading: expensesLoading,
    isError: expensesError,
  } = useExpenses({ year, month })
  const { data: projected, isLoading: projectedLoading } = useRecurringProjection({
    year,
    month,
  })
  const {
    data: categories,
    isLoading: categoriesLoading,
    isError: categoriesError,
  } = useCategories()
  // Same query the dashboard summary already fetches for this month/scope --
  // shares its cache entry, so this doesn't add a network request. Used only
  // for its base_currency, which totals in a different currency than "PHP"
  // need (BUD-53).
  const { data: summary } = useDashboardSummary({ year, month })
  const baseCurrency = summary?.base_currency ?? "PHP"
  const isLoading = expensesLoading || categoriesLoading || projectedLoading
  const deleteExpense = useDeleteExpense()
  const filter = useExpenseFilterStore((state) => state.filter)

  const [editTarget, setEditTarget] = useState<Expense | undefined>(undefined)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [actionTarget, setActionTarget] = useState<Expense | null>(null)
  const [deleteErrors, setDeleteErrors] = useState<Record<string, string>>({})
  const [pendingDeleteIds, setPendingDeleteIds] = useState<Set<string>>(
    new Set()
  )

  const categoryById = useMemo(
    () =>
      new Map((categories ?? []).map((category) => [category.id, category])),
    [categories]
  )

  const monthExpenses = useMemo(
    () => mergeProjectedExpenses(expenses ?? [], projected),
    [expenses, projected]
  )

  const filteredExpenses = useMemo(
    () =>
      monthExpenses.filter((expense) =>
        matchesFilter(filter, expense, categoryById.get(expense.category_id))
      ),
    [monthExpenses, filter, categoryById]
  )

  // Summed in the base currency (base_amount), not the original amount --
  // expenses can be recorded in different currencies, so summing `amount`
  // directly would add unlike units together (BUD-53).
  const filteredTotal = useMemo(
    () =>
      filteredExpenses.reduce(
        (cents, expense) =>
          expense.isProjected
            ? cents
            : cents + Math.round(Number(expense.base_amount) * 100),
        0
      ) / 100,
    [filteredExpenses]
  )

  const filterLabel = getFilterLabel(filter, categoryById)

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
      await deleteExpense.mutateAsync({ id: expense.id })
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

  function handleDeleteClick(expense: Expense) {
    if (expense.installment_group_id || expense.recurring_expense_id) {
      setActionTarget(expense)
    } else {
      handleDelete(expense)
    }
  }

  return (
    <section className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold tracking-tight">Expenses</h2>
        {!isLoading && !expensesError && (
          <span className="text-sm font-semibold">
            {formatCurrency(filteredTotal, baseCurrency)}
          </span>
        )}
      </div>

      <ExpenseFilterBar />

      {isLoading && <p className="text-sm text-muted-foreground">Loading…</p>}

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

      {!isLoading && !expensesError && monthExpenses.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No expenses recorded for{" "}
          {formatMonthLabel(year, month)}.
        </p>
      )}

      {!isLoading &&
        !expensesError &&
        monthExpenses.length > 0 &&
        filteredExpenses.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No {filterLabel} expenses for{" "}
            {formatMonthLabel(year, month)}.
          </p>
        )}

      {!isLoading && !expensesError && filteredExpenses.length > 0 && (
        <ul className="flex flex-col gap-2">
          {filteredExpenses.map((expense) => {
            const category = categoryById.get(expense.category_id)
            const isInstallment = !!expense.installment_group_id
            const isRecurringSourced = !!expense.recurring_expense_id
            const displayDescription = expense.original_description ?? expense.description

            return (
              <li key={expense.id} className="flex flex-col gap-1">
                <div
                  className={cn(
                    "flex items-center gap-3 rounded-2xl border bg-card px-4 py-3",
                    expense.isProjected && "border-dashed opacity-70"
                  )}
                >
                  <CategoryColor
                    color={category?.color ?? "#9ca3af"}
                    className="size-5"
                  />

                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="truncate text-sm font-medium">
                        {displayDescription}
                      </span>
                      <span className="shrink-0 text-xs text-muted-foreground">
                        {category?.name ?? "Uncategorized"}
                      </span>
                      {isInstallment && (
                        <Badge variant="outline">
                          {expense.installment_index}/{expense.installment_total}
                        </Badge>
                      )}
                      {isRecurringSourced && (
                        <Badge variant={expense.isProjected ? "secondary" : "outline"}>
                          {expense.isProjected ? "Upcoming" : "Recurring"}
                        </Badge>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {formatExpenseDate(expense.spent_on)}
                    </span>
                  </div>

                  <ExpenseAmount expense={expense} baseCurrency={baseCurrency} />

                  <div className="flex shrink-0 items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      aria-label={`Edit ${displayDescription}`}
                      onClick={() => openEdit(expense)}
                      disabled={expense.isProjected}
                    >
                      <PencilIcon />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      aria-label={
                        isRecurringSourced
                          ? `Stop recurring expense ${displayDescription}`
                          : `Delete ${displayDescription}`
                      }
                      onClick={() => handleDeleteClick(expense)}
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

      <ExpenseActionDialog
        target={actionTarget}
        month={{ year, month }}
        onOpenChange={(open) => {
          if (!open) {
            setActionTarget(null)
          }
        }}
      />
    </section>
  )
}

export { ExpenseList }
