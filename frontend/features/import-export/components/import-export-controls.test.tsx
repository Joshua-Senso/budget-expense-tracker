import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen } from "@testing-library/react"
import { beforeEach, expect, test } from "vitest"

import { useWorkspaceStore } from "@/stores/workspace-store"

import { ImportExportControls } from "./import-export-controls"

function renderControls() {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <ImportExportControls />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  useWorkspaceStore.setState({ activeWorkspaceId: null, activeWorkspaceScope: "personal" })
})

test("shows export/import buttons in the personal workspace", () => {
  renderControls()

  expect(screen.getByRole("button", { name: "Export" })).toBeInTheDocument()
  expect(screen.getByRole("button", { name: "Import" })).toBeInTheDocument()
})

test("hides export/import buttons and shows a personal-only note in a household workspace", () => {
  useWorkspaceStore.setState({ activeWorkspaceId: "house-1", activeWorkspaceScope: "household" })

  renderControls()

  expect(screen.queryByRole("button", { name: "Export" })).not.toBeInTheDocument()
  expect(screen.queryByRole("button", { name: "Import" })).not.toBeInTheDocument()
  expect(screen.getByText(/personal workspace only/i)).toBeInTheDocument()
})
