"use client"

import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { formatMonthLabel } from "@/lib/format"
import { useMonthStore } from "@/stores/month-store"

function MonthNav() {
  const year = useMonthStore((state) => state.year)
  const month = useMonthStore((state) => state.month)
  const shiftMonth = useMonthStore((state) => state.shiftMonth)

  return (
    <div className="flex items-center justify-between">
      <h1 className="text-3xl font-semibold tracking-tight">
        {formatMonthLabel(year, month)}
      </h1>
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label="Previous month"
          onClick={() => shiftMonth(-1)}
        >
          <ChevronLeftIcon />
        </Button>
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label="Next month"
          onClick={() => shiftMonth(1)}
        >
          <ChevronRightIcon />
        </Button>
      </div>
    </div>
  )
}

export { MonthNav }
