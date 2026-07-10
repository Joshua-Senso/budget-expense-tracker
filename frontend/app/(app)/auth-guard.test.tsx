import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import { beforeEach, expect, test, vi } from "vitest"

const guardMocks = vi.hoisted(() => ({
  replace: vi.fn(),
  useSession: vi.fn(),
  clearBearerToken: vi.fn(),
}))

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: guardMocks.replace }),
}))

vi.mock("@/lib/auth-client", () => ({
  authClient: {
    useSession: guardMocks.useSession,
    signOut: vi.fn(),
  },
  clearBearerToken: guardMocks.clearBearerToken,
}))

import { AuthGuard } from "./auth-guard"

function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient()
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  )
}

beforeEach(() => {
  guardMocks.replace.mockReset()
  guardMocks.useSession.mockReset()
  guardMocks.clearBearerToken.mockReset()
})

test("auth guard shows a loading state while the session is pending", () => {
  guardMocks.useSession.mockReturnValue({ data: null, isPending: true })

  renderWithQueryClient(
    <AuthGuard>
      <p>Dashboard</p>
    </AuthGuard>,
  )

  expect(screen.getByText("Loading your workspace...")).toBeInTheDocument()
})

test("auth guard redirects unauthenticated users", async () => {
  guardMocks.useSession.mockReturnValue({ data: null, isPending: false })

  renderWithQueryClient(
    <AuthGuard>
      <p>Dashboard</p>
    </AuthGuard>,
  )

  await waitFor(() => {
    expect(guardMocks.replace).toHaveBeenCalledWith("/sign-in")
  })
  expect(screen.queryByText("Dashboard")).not.toBeInTheDocument()
})

test("auth guard renders authenticated children", () => {
  guardMocks.useSession.mockReturnValue({
    data: { user: { id: "user-1" } },
    isPending: false,
  })

  renderWithQueryClient(
    <AuthGuard>
      <p>Dashboard</p>
    </AuthGuard>,
  )

  expect(screen.getByText("Dashboard")).toBeInTheDocument()
})
