import { create } from "zustand"

type YearState = {
  year: number
  setYear: (year: number) => void
  shiftYear: (delta: number) => void
}

function getCurrentYear(): number {
  return new Date().getFullYear()
}

const useYearStore = create<YearState>((set, get) => ({
  year: getCurrentYear(),
  setYear: (year) => set({ year }),
  shiftYear: (delta) => set({ year: get().year + delta }),
}))

export { useYearStore, getCurrentYear }
