import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import { beforeEach, expect, test, vi } from "vitest"

import { useWorkspaceStore } from "@/stores/workspace-store"

const authMocks = vi.hoisted(() => ({
  useSession: vi.fn(),
  useListOrganizations: vi.fn(),
  updateUser: vi.fn(),
  organizationUpdate: vi.fn(),
}))

const themeMocks = vi.hoisted(() => ({
  setTheme: vi.fn(),
}))

vi.mock("@/lib/auth-client", () => ({
  authClient: {
    useSession: authMocks.useSession,
    useListOrganizations: authMocks.useListOrganizations,
    updateUser: authMocks.updateUser,
    organization: {
      update: authMocks.organizationUpdate,
    },
  },
}))

vi.mock("next-themes", () => ({
  useTheme: () => ({ setTheme: themeMocks.setTheme }),
}))

import { ThemePicker } from "./theme-picker"

function renderPicker() {
  const queryClient = new QueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <ThemePicker />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  authMocks.useSession.mockReset()
  authMocks.useListOrganizations.mockReset()
  authMocks.updateUser.mockReset()
  authMocks.organizationUpdate.mockReset()
  themeMocks.setTheme.mockReset()

  authMocks.useListOrganizations.mockReturnValue({
    data: [{ id: "house-1", name: "The Household", slug: "the-household", theme: "light" }],
    error: null,
    isPending: false,
  })

  useWorkspaceStore.setState({
    activeWorkspaceId: null,
    activeWorkspaceScope: "personal",
  })
})

test("shows the personal theme and updates the user record on change", async () => {
  authMocks.useSession.mockReturnValue({
    data: { user: { id: "user-1", theme: "dark" } },
    isPending: false,
  })
  authMocks.updateUser.mockResolvedValue({ data: { theme: "light" }, error: null })

  renderPicker()

  expect(screen.getByRole("combobox")).toHaveTextContent("Warm Dark")
  expect(screen.getByText("Applies only to your personal workspace.")).toBeInTheDocument()
})

test("shows the household theme and updates the organization record on change", async () => {
  authMocks.useSession.mockReturnValue({
    data: { user: { id: "user-1", theme: "dark" } },
    isPending: false,
  })
  authMocks.organizationUpdate.mockResolvedValue({ data: { theme: "dark" }, error: null })
  useWorkspaceStore.getState().setActiveWorkspace({ id: "house-1" })

  renderPicker()

  expect(screen.getByRole("combobox")).toHaveTextContent("Light")
  expect(screen.getByText("Applies to everyone in The Household.")).toBeInTheDocument()
})

test("applies the new theme immediately, before the mutation resolves", async () => {
  authMocks.useSession.mockReturnValue({
    data: { user: { id: "user-1", theme: "dark" } },
    isPending: false,
  })
  let resolveUpdate: (value: { data: unknown; error: null }) => void = () => {}
  authMocks.updateUser.mockReturnValue(
    new Promise((resolve) => {
      resolveUpdate = resolve
    }),
  )

  renderPicker()

  const { fireEvent } = await import("@testing-library/react")
  fireEvent.click(screen.getByRole("combobox"))
  fireEvent.click(await screen.findByText("Light"))

  expect(themeMocks.setTheme).toHaveBeenCalledWith("light")
  await waitFor(() => {
    expect(authMocks.updateUser).toHaveBeenCalledWith({ theme: "light" })
  })

  resolveUpdate({ data: { theme: "light" }, error: null })
})

test("reverts the applied theme if saving fails", async () => {
  authMocks.useSession.mockReturnValue({
    data: { user: { id: "user-1", theme: "dark" } },
    isPending: false,
  })
  authMocks.updateUser.mockResolvedValue({ data: null, error: { message: "network error" } })

  renderPicker()

  const { fireEvent } = await import("@testing-library/react")
  fireEvent.click(screen.getByRole("combobox"))
  fireEvent.click(await screen.findByText("Light"))

  await waitFor(() => {
    expect(themeMocks.setTheme).toHaveBeenCalledWith("dark")
  })
  expect(screen.getByText("network error")).toBeInTheDocument()
})
