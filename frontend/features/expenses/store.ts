import { useEffect } from "react"
import { create } from "zustand"

import { useWorkspaceStore } from "@/stores/workspace-store"

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

// A category filter's categoryId is scoped to whichever workspace it was set
// in and usually doesn't exist in a different workspace -- left stale across
// a workspace switch, it would render a misleadingly empty list with no
// indication a stale filter (not an actually-empty month) is the cause.
function useResetExpenseFilterOnWorkspaceChange() {
  const setFilter = useExpenseFilterStore((state) => state.setFilter)
  const activeWorkspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)

  useEffect(() => {
    setFilter({ type: "all" })
  }, [activeWorkspaceId, setFilter])
}

export { useExpenseFilterStore, useResetExpenseFilterOnWorkspaceChange }
export type { ExpenseFilter }
