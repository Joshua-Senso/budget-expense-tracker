import { create } from "zustand"

type SelectedMonth = {
  year: number
  month: number
}

type MonthState = SelectedMonth & {
  setMonth: (month: SelectedMonth) => void
  shiftMonth: (delta: number) => void
}

function getCurrentMonth(): SelectedMonth {
  const now = new Date()

  return { year: now.getFullYear(), month: now.getMonth() + 1 }
}

function shiftMonth(
  { year, month }: SelectedMonth,
  delta: number
): SelectedMonth {
  const date = new Date(Date.UTC(year, month - 1 + delta, 1))

  return { year: date.getUTCFullYear(), month: date.getUTCMonth() + 1 }
}

function toMonthKey({ year, month }: SelectedMonth): string {
  return `${year}-${String(month).padStart(2, "0")}`
}

const useMonthStore = create<MonthState>((set, get) => ({
  ...getCurrentMonth(),
  setMonth: (month) => set(month),
  shiftMonth: (delta) => set(shiftMonth(get(), delta)),
}))

export { useMonthStore, toMonthKey, getCurrentMonth }
export type { SelectedMonth }
