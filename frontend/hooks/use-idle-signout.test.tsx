import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { renderHook } from "@testing-library/react"
import { afterEach, beforeEach, expect, test, vi } from "vitest"
import type { ReactNode } from "react"

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

import { useIdleSignout } from "./use-idle-signout"

const IDLE_MS = 30 * 60 * 1000
const CHECK_INTERVAL_MS = 60_000

function renderIdleSignout(queryClient: QueryClient) {
  function wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }

  return renderHook(() => useIdleSignout({ enabled: true }), { wrapper })
}

beforeEach(() => {
  vi.useFakeTimers()
  authMocks.signOut.mockReset()
  authMocks.clearBearerToken.mockReset()
  routerMocks.replace.mockReset()
  useWorkspaceStore.setState({ activeWorkspaceId: null, activeWorkspaceScope: "personal" })
})

afterEach(() => {
  vi.useRealTimers()
})

test("clears the cached bearer token and query cache before redirecting, once the user goes idle", async () => {
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

  const queryClient = new QueryClient()
  const clearSpy = vi.spyOn(queryClient, "clear").mockImplementation(() => {
    callOrder.push("queryClient.clear")
  })

  renderIdleSignout(queryClient)

  await vi.advanceTimersByTimeAsync(IDLE_MS + CHECK_INTERVAL_MS)

  expect(authMocks.signOut).toHaveBeenCalledTimes(1)
  expect(authMocks.clearBearerToken).toHaveBeenCalledTimes(1)
  expect(clearSpy).toHaveBeenCalledTimes(1)
  expect(routerMocks.replace).toHaveBeenCalledWith("/sign-in")
  // Session/query state must be cleared before the redirect, or a fast
  // sign-in by a second user on the same device could still see it.
  expect(callOrder).toEqual(["signOut", "clearBearerToken", "queryClient.clear", "replace"])
})

test("does not sign out while the user remains active", async () => {
  const queryClient = new QueryClient()
  renderIdleSignout(queryClient)

  await vi.advanceTimersByTimeAsync(CHECK_INTERVAL_MS * 2)

  expect(authMocks.signOut).not.toHaveBeenCalled()
  expect(routerMocks.replace).not.toHaveBeenCalled()
})
