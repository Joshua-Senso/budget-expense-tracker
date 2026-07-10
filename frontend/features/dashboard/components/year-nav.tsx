"use client"

import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useYearStore } from "@/stores/year-store"

function YearNav() {
  const year = useYearStore((state) => state.year)
  const shiftYear = useYearStore((state) => state.shiftYear)

  return (
    <div className="flex items-center justify-between">
      <h1 className="text-3xl font-semibold tracking-tight">{year}</h1>
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label="Previous year"
          onClick={() => shiftYear(-1)}
        >
          <ChevronLeftIcon />
        </Button>
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label="Next year"
          onClick={() => shiftYear(1)}
        >
          <ChevronRightIcon />
        </Button>
      </div>
    </div>
  )
}

export { YearNav }
