import { create } from "zustand"

type ExpenseFilter =
  | { type: "all" }
  | { type: "card" }
  | { type: "other" }
  | { type: "category"; categoryId: string }

type ExpenseFilterState = {
  filter: ExpenseFilter
  setFilter: (filter: ExpenseFilter) => void
}

const useExpenseFilterStore = create<ExpenseFilterState>((set) => ({
  filter: { type: "all" },
  setFilter: (filter) => set({ filter }),
}))

export { useExpenseFilterStore }
export type { ExpenseFilter }
