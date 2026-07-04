"use client"

import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { CategoryColor, useCategories } from "@/features/categories"

import { useExpenseFilterStore } from "../store"

const GROUP_FILTERS = [
  { type: "all", label: "All" },
  { type: "card", label: "Card" },
  { type: "other", label: "Other" },
] as const

function ExpenseFilterBar() {
  const { data: categories } = useCategories()
  const filter = useExpenseFilterStore((state) => state.filter)
  const setFilter = useExpenseFilterStore((state) => state.setFilter)

  return (
    <div className="flex flex-wrap items-center gap-2">
      {GROUP_FILTERS.map(({ type, label }) => (
        <Button
          key={type}
          type="button"
          size="sm"
          variant={filter.type === type ? "default" : "outline"}
          aria-pressed={filter.type === type}
          onClick={() => setFilter({ type })}
        >
          {label}
        </Button>
      ))}

      <Select
        value={filter.type === "category" ? filter.categoryId : ""}
        onValueChange={(categoryId) => setFilter({ type: "category", categoryId })}
      >
        <SelectTrigger className="w-44">
          <SelectValue placeholder="By category" />
        </SelectTrigger>
        <SelectContent>
          {(categories ?? []).map((category) => (
            <SelectItem key={category.id} value={category.id}>
              <CategoryColor color={category.color} className="size-3" />
              {category.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

export { ExpenseFilterBar }
