import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen } from "@testing-library/react"
import { beforeEach, expect, test, vi } from "vitest"

import { useWorkspaceStore } from "@/stores/workspace-store"

import type { DashboardSummaryData } from "../schemas"

const dashboardMocks = vi.hoisted(() => ({
  useDashboardSummary: vi.fn(),
}))

vi.mock("../api/queries", () => ({
  useDashboardSummary: dashboardMocks.useDashboardSummary,
}))

vi.mock("@/features/budget/api/queries", () => ({
  useMonthlySetting: () => ({ data: null, isLoading: false, isError: false }),
}))

vi.mock("@/features/budget/api/mutations", () => ({
  useUpsertMonthlySetting: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
    isError: false,
  }),
}))

import { DashboardSummary } from "./dashboard-summary"

function baseSummary(): DashboardSummaryData {
  return {
    month_key: "2026-01",
    card: { total: "0", categories: [] },
    other: { total: "0", categories: [] },
    month_total: "0",
    monthly_net_salary: null,
    remaining: null,
    percent_used: null,
    base_currency: "PHP",
  }
}

function renderSummary() {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <DashboardSummary />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  useWorkspaceStore.setState({ activeWorkspaceId: null, activeWorkspaceScope: "personal" })
  dashboardMocks.useDashboardSummary.mockReturnValue({
    data: baseSummary(),
    isLoading: false,
    isError: false,
  })
})

test("shows the salary input in the personal workspace", () => {
  renderSummary()

  expect(screen.getByLabelText("Monthly net salary")).toBeInTheDocument()
})

test("hides the salary input and shows a household note in a household workspace", () => {
  useWorkspaceStore.setState({ activeWorkspaceId: "house-1", activeWorkspaceScope: "household" })

  renderSummary()

  expect(screen.queryByLabelText("Monthly net salary")).not.toBeInTheDocument()
  expect(screen.getByText(/household budgets aren.t supported yet/i)).toBeInTheDocument()
})
