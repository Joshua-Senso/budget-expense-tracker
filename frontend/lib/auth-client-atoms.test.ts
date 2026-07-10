import { act, renderHook, waitFor } from "@testing-library/react"
import { afterEach, beforeEach, expect, test, vi } from "vitest"

// Regression coverage for the assumption `features/theme`'s mutations rely
// on: Better Auth's client refreshes `useSession()`/`useListOrganizations()`
// on its own after `/update-user` and `/organization/update` (see the
// atomListeners wiring in better-auth's client config/organization plugin),
// so the theme mutations don't need to manually invalidate anything. This
// exercises the real (unmocked) authClient against a fake fetch, rather than
// asserting the mechanism only in a comment.

type State = {
  theme: string
  org: { id: string; name: string; slug: string; theme: string }
}

let state: State

function jsonResponse(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "content-type": "application/json" },
  })
}

const fetchMock = vi.fn(async (input: unknown, init?: RequestInit) => {
  const url = String(input)
  const method = init?.method ?? "GET"
  const body = init?.body ? JSON.parse(init.body as string) : undefined

  if (url.includes("/get-session")) {
    return jsonResponse({ session: { id: "session-1" }, user: { id: "user-1", theme: state.theme } })
  }
  if (url.includes("/update-user") && method === "POST") {
    state.theme = body.theme
    return jsonResponse({ status: true })
  }
  if (url.includes("/organization/list")) {
    return jsonResponse([state.org])
  }
  if (url.includes("/organization/update") && method === "POST") {
    state.org = { ...state.org, ...body.data }
    return jsonResponse(state.org)
  }

  return jsonResponse({})
})

beforeEach(() => {
  state = {
    theme: "dark",
    org: { id: "house-1", name: "The Household", slug: "the-household", theme: "dark" },
  }
  vi.stubGlobal("fetch", fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.resetModules()
})

test("useSession refreshes automatically after updateUser, with no manual invalidation", async () => {
  const { authClient } = await import("./auth-client")

  const { result } = renderHook(() => authClient.useSession())

  await waitFor(() => expect(result.current.data?.user.theme).toBe("dark"))

  await act(async () => {
    await authClient.updateUser({ theme: "light" })
  })

  await waitFor(() => expect(result.current.data?.user.theme).toBe("light"))
})

test("useListOrganizations refreshes automatically after organization.update, with no manual invalidation", async () => {
  const { authClient } = await import("./auth-client")

  const { result } = renderHook(() => authClient.useListOrganizations())

  await waitFor(() => expect(result.current.data?.[0]?.theme).toBe("dark"))

  await act(async () => {
    await authClient.organization.update({
      organizationId: "house-1",
      data: { theme: "light" },
    })
  })

  await waitFor(() => expect(result.current.data?.[0]?.theme).toBe("light"))
})
