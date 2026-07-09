import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { beforeEach, expect, test, vi } from "vitest"

import { useWorkspaceStore } from "@/stores/workspace-store"

const authMocks = vi.hoisted(() => ({
  signOut: vi.fn(),
  clearBearerToken: vi.fn(),
}))

const routerMocks = vi.hoisted(() => ({
  replace: vi.fn(),
}))

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: routerMocks.replace }),
}))

vi.mock("@/lib/auth-client", () => ({
  authClient: { signOut: authMocks.signOut },
  clearBearerToken: authMocks.clearBearerToken,
}))

import { SignOutButton } from "./sign-out-button"

function renderButton() {
  const queryClient = new QueryClient()
  const clearSpy = vi.spyOn(queryClient, "clear")
  render(
    <QueryClientProvider client={queryClient}>
      <SignOutButton />
    </QueryClientProvider>,
  )
  return { clearSpy }
}

beforeEach(() => {
  authMocks.signOut.mockReset()
  authMocks.clearBearerToken.mockReset()
  routerMocks.replace.mockReset()
  useWorkspaceStore.setState({ activeWorkspaceId: null, activeWorkspaceScope: "personal" })
})

test("clears the cached bearer token and query cache before redirecting to sign-in", async () => {
  const callOrder: string[] = []
  authMocks.signOut.mockImplementation(async () => {
    callOrder.push("signOut")
  })
  authMocks.clearBearerToken.mockImplementation(() => {
    callOrder.push("clearBearerToken")
  })
  routerMocks.replace.mockImplementation(() => {
    callOrder.push("replace")
  })

  const { clearSpy } = renderButton()
  clearSpy.mockImplementation(() => {
    callOrder.push("queryClient.clear")
  })

  fireEvent.click(screen.getByRole("button", { name: "Sign out" }))

  await waitFor(() => {
    expect(routerMocks.replace).toHaveBeenCalledWith("/sign-in")
  })

  expect(authMocks.clearBearerToken).toHaveBeenCalledTimes(1)
  expect(clearSpy).toHaveBeenCalledTimes(1)
  // Session/query state must be cleared before the redirect, or a fast
  // sign-in by a second user on the same device could still see it.
  expect(callOrder).toEqual(["signOut", "clearBearerToken", "queryClient.clear", "replace"])
})

test("resets the active workspace on sign-out", async () => {
  useWorkspaceStore.setState({ activeWorkspaceId: "house-1", activeWorkspaceScope: "household" })
  authMocks.signOut.mockResolvedValue(undefined)

  renderButton()
  fireEvent.click(screen.getByRole("button", { name: "Sign out" }))

  await waitFor(() => {
    expect(routerMocks.replace).toHaveBeenCalledWith("/sign-in")
  })

  expect(useWorkspaceStore.getState().activeWorkspaceId).toBeNull()
})
