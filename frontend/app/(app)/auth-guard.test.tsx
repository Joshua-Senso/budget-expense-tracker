import { render, screen, waitFor } from "@testing-library/react"
import { beforeEach, expect, test, vi } from "vitest"

const guardMocks = vi.hoisted(() => ({
  replace: vi.fn(),
  useSession: vi.fn(),
}))

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: guardMocks.replace }),
}))

vi.mock("@/lib/auth-client", () => ({
  authClient: {
    useSession: guardMocks.useSession,
  },
}))

import { AuthGuard } from "./auth-guard"

beforeEach(() => {
  guardMocks.replace.mockReset()
  guardMocks.useSession.mockReset()
})

test("auth guard shows a loading state while the session is pending", () => {
  guardMocks.useSession.mockReturnValue({ data: null, isPending: true })

  render(
    <AuthGuard>
      <p>Dashboard</p>
    </AuthGuard>,
  )

  expect(screen.getByText("Loading your workspace...")).toBeInTheDocument()
})

test("auth guard redirects unauthenticated users", async () => {
  guardMocks.useSession.mockReturnValue({ data: null, isPending: false })

  render(
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

  render(
    <AuthGuard>
      <p>Dashboard</p>
    </AuthGuard>,
  )

  expect(screen.getByText("Dashboard")).toBeInTheDocument()
})
