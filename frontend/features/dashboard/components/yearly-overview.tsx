"use client"

import { useState } from "react"
import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { formatCurrency, formatMonthName } from "@/lib/format"
import { useYearStore } from "@/stores/year-store"

import { useYearlyOverview } from "../api/queries"
import type { MonthlyOverview } from "../schemas"

const WINDOW_SIZE = 3
const QUARTER_LABELS = ["1st Quarter", "2nd Quarter", "3rd Quarter", "4th Quarter"]

function chunkMonths(months: MonthlyOverview[]): MonthlyOverview[][] {
  const windows: MonthlyOverview[][] = []
  for (let i = 0; i < months.length; i += WINDOW_SIZE) {
    windows.push(months.slice(i, i + WINDOW_SIZE))
  }
  return windows
}

function MonthTile({ month }: { month: MonthlyOverview }) {
  return (
    <div className="flex flex-col gap-3 rounded-3xl border bg-card p-5 shadow-sm">
      <div className="flex items-baseline justify-between">
        <h3 className="text-sm font-medium text-muted-foreground uppercase">
          {formatMonthName(month.month)}
        </h3>
        <span className="text-xl font-semibold">
          {formatCurrency(month.month_total, "PHP")}
        </span>
      </div>

      <ul className="flex flex-col gap-1.5">
        <li className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Card</span>
          <span className="font-medium">
            {formatCurrency(month.card_total, "PHP")}
          </span>
        </li>
        <li className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Other</span>
          <span className="font-medium">
            {formatCurrency(month.other_total, "PHP")}
          </span>
        </li>
      </ul>
    </div>
  )
}

function YearlyOverview() {
  const year = useYearStore((state) => state.year)
  const { data: overview, isLoading, isError } = useYearlyOverview(year)
  const [windowIndex, setWindowIndex] = useState(0)
  const [prevYear, setPrevYear] = useState(year)

  if (year !== prevYear) {
    setPrevYear(year)
    setWindowIndex(0)
  }

  if (isLoading) {
    return (
      <p className="text-sm text-muted-foreground">
        Loading yearly overview…
      </p>
    )
  }

  if (isError || !overview) {
    return (
      <p className="text-sm text-destructive" role="alert">
        Failed to load the yearly overview.
      </p>
    )
  }

  const windows = chunkMonths(overview.months)
  const currentWindow = windows[windowIndex] ?? []

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-muted-foreground uppercase">
          {QUARTER_LABELS[windowIndex]}
        </h2>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Previous quarter"
            disabled={windowIndex === 0}
            onClick={() => setWindowIndex((index) => index - 1)}
          >
            <ChevronLeftIcon />
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Next quarter"
            disabled={windowIndex === windows.length - 1}
            onClick={() => setWindowIndex((index) => index + 1)}
          >
            <ChevronRightIcon />
          </Button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {currentWindow.map((month) => (
          <MonthTile key={month.month_key} month={month} />
        ))}
      </div>

      <div className="flex items-center justify-between rounded-3xl border bg-card p-5 shadow-sm">
        <h3 className="text-sm font-medium text-muted-foreground uppercase">
          Year total
        </h3>
        <span className="text-xl font-semibold">
          {formatCurrency(overview.year_total, "PHP")}
        </span>
      </div>
    </div>
  )
}

export { YearlyOverview }
