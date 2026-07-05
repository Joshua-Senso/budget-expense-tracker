"use client"

import { useState } from "react"

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { useStopRecurringExpense } from "@/features/recurring"
import { ApiError } from "@/lib/api-client"
import { formatMonthLabel } from "@/lib/format"
import { toMonthKey } from "@/stores/month-store"
import type { SelectedMonth } from "@/stores/month-store"

import { useDeleteExpense } from "../api/mutations"
import type { Expense } from "../schemas"

function getStopErrorMessage(err: unknown) {
  if (err instanceof ApiError && err.status === 404) {
    return "This recurring expense no longer exists. Refresh the page and try again."
  }

  return "Could not stop this recurring expense. Please try again."
}

function getDeleteErrorMessage(err: unknown) {
  if (err instanceof ApiError && err.status === 404) {
    return "This expense no longer exists. Refresh the page and try again."
  }

  return "Could not delete expense. Please try again."
}

interface ExpenseActionDialogProps {
  target: Expense | null
  month: SelectedMonth
  onOpenChange: (open: boolean) => void
}

function ExpenseActionDialog({ target, month, onOpenChange }: ExpenseActionDialogProps) {
  const deleteExpense = useDeleteExpense()
  const stopRecurring = useStopRecurringExpense()
  const [error, setError] = useState<string | null>(null)
  // Keeps rendering the last real target's content while the dialog plays its
  // close animation, instead of flashing to the wrong branch once `target`
  // is cleared out from under a still-visible dialog. Adjusted during render
  // (not an effect) per React's "adjusting state when a prop changes" pattern.
  const [prevTarget, setPrevTarget] = useState(target)
  const [displayTarget, setDisplayTarget] = useState(target)
  if (target !== prevTarget) {
    setPrevTarget(target)
    if (target) {
      setDisplayTarget(target)
    }
  }

  const isRecurring = !!displayTarget?.recurring_expense_id
  const isPending = deleteExpense.isPending || stopRecurring.isPending

  function handleOpenChange(open: boolean) {
    if (!open) {
      setError(null)
    }
    onOpenChange(open)
  }

  async function handleStop() {
    if (!target?.recurring_expense_id) {
      return
    }
    setError(null)
    try {
      await stopRecurring.mutateAsync({
        id: target.recurring_expense_id,
        monthKey: toMonthKey(month),
      })
      handleOpenChange(false)
    } catch (err) {
      setError(getStopErrorMessage(err))
    }
  }

  async function handleDelete(scope: "row" | "group") {
    if (!target) {
      return
    }
    setError(null)
    try {
      await deleteExpense.mutateAsync({ id: target.id, scope })
      handleOpenChange(false)
    } catch (err) {
      setError(getDeleteErrorMessage(err))
    }
  }

  return (
    <AlertDialog open={!!target} onOpenChange={handleOpenChange}>
      <AlertDialogContent size={isRecurring ? "default" : "sm"}>
        {isRecurring ? (
          <>
            <AlertDialogHeader>
              <AlertDialogTitle>Stop this recurring expense?</AlertDialogTitle>
              <AlertDialogDescription>
                This stops &ldquo;{displayTarget?.description}&rdquo; from{" "}
                {formatMonthLabel(month.year, month.month)} onward. Past months and this
                month&apos;s entry are kept.
              </AlertDialogDescription>
            </AlertDialogHeader>
            {error && (
              <p className="text-sm text-destructive" role="alert">
                {error}
              </p>
            )}
            <AlertDialogFooter>
              <AlertDialogCancel disabled={isPending}>Cancel</AlertDialogCancel>
              <AlertDialogAction
                variant="destructive"
                disabled={isPending}
                onClick={(event) => {
                  event.preventDefault()
                  handleStop()
                }}
              >
                Stop recurring
              </AlertDialogAction>
            </AlertDialogFooter>
          </>
        ) : (
          <>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete this installment?</AlertDialogTitle>
              <AlertDialogDescription>
                &ldquo;{displayTarget?.original_description ?? displayTarget?.description}
                &rdquo; is installment {displayTarget?.installment_index} of{" "}
                {displayTarget?.installment_total}. Choose whether to delete just this
                installment or the entire series.
              </AlertDialogDescription>
            </AlertDialogHeader>
            {error && (
              <p className="text-sm text-destructive" role="alert">
                {error}
              </p>
            )}
            <AlertDialogFooter>
              <AlertDialogCancel disabled={isPending}>Cancel</AlertDialogCancel>
              <AlertDialogAction
                variant="outline"
                disabled={isPending}
                onClick={(event) => {
                  event.preventDefault()
                  handleDelete("row")
                }}
              >
                Delete this installment
              </AlertDialogAction>
              <AlertDialogAction
                variant="destructive"
                disabled={isPending}
                onClick={(event) => {
                  event.preventDefault()
                  handleDelete("group")
                }}
              >
                Delete entire series
              </AlertDialogAction>
            </AlertDialogFooter>
          </>
        )}
      </AlertDialogContent>
    </AlertDialog>
  )
}

export { ExpenseActionDialog, getDeleteErrorMessage }
