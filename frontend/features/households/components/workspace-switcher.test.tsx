import { render, screen, waitFor } from "@testing-library/react"
import { beforeEach, expect, test, vi } from "vitest"

import { useWorkspaceStore } from "@/stores/workspace-store"

const householdMocks = vi.hoisted(() => ({
  useListOrganizations: vi.fn(),
}))

vi.mock("@/lib/auth-client", () => ({
  authClient: {
    useListOrganizations: householdMocks.useListOrganizations,
  },
}))

import { WorkspaceSwitcher } from "./workspace-switcher"

beforeEach(() => {
  householdMocks.useListOrganizations.mockReset()
  useWorkspaceStore.setState({
    activeWorkspaceId: null,
    activeWorkspaceScope: "personal",
  })
})

test("defaults to Personal when no workspace is active", () => {
  householdMocks.useListOrganizations.mockReturnValue({
    data: [{ id: "house-1", name: "The Household", slug: "the-household" }],
    error: null,
    isPending: false,
  })

  render(<WorkspaceSwitcher />)

  expect(screen.getByRole("combobox")).toHaveTextContent("Personal")
})

test("reflects the active household once households load", () => {
  useWorkspaceStore.getState().setActiveWorkspace({ id: "house-1" })
  householdMocks.useListOrganizations.mockReturnValue({
    data: [{ id: "house-1", name: "The Household", slug: "the-household" }],
    error: null,
    isPending: false,
  })

  render(<WorkspaceSwitcher />)

  expect(screen.getByRole("combobox")).toHaveTextContent("The Household")
  expect(useWorkspaceStore.getState()).toMatchObject({
    activeWorkspaceId: "house-1",
    activeWorkspaceScope: "household",
  })
})

test("falls back to personal scope when the active household disappears from the list", async () => {
  useWorkspaceStore.getState().setActiveWorkspace({ id: "stale-household" })
  householdMocks.useListOrganizations.mockReturnValue({
    data: [{ id: "house-1", name: "The Household", slug: "the-household" }],
    error: null,
    isPending: false,
  })

  render(<WorkspaceSwitcher />)

  await waitFor(() => {
    expect(useWorkspaceStore.getState()).toMatchObject({
      activeWorkspaceId: null,
      activeWorkspaceScope: "personal",
    })
  })
})

test("does not reset the active household while it is still loading", () => {
  useWorkspaceStore.getState().setActiveWorkspace({ id: "house-1" })
  householdMocks.useListOrganizations.mockReturnValue({
    data: undefined,
    error: null,
    isPending: true,
  })

  render(<WorkspaceSwitcher />)

  expect(useWorkspaceStore.getState()).toMatchObject({
    activeWorkspaceId: "house-1",
    activeWorkspaceScope: "household",
  })
})

test("falls back to personal scope if the household list fails to load", async () => {
  useWorkspaceStore.getState().setActiveWorkspace({ id: "house-1" })
  householdMocks.useListOrganizations.mockReturnValue({
    data: undefined,
    error: { message: "network error" },
    isPending: false,
  })

  render(<WorkspaceSwitcher />)

  await waitFor(() => {
    expect(useWorkspaceStore.getState()).toMatchObject({
      activeWorkspaceId: null,
      activeWorkspaceScope: "personal",
    })
  })
})
