import { beforeEach, describe, expect, test, vi } from "vitest"

const betterAuthMocks = vi.hoisted(() => ({
  fetch: vi.fn(),
}))

vi.mock("better-auth/react", () => ({
  createAuthClient: () => ({
    $fetch: betterAuthMocks.fetch,
    useSession: vi.fn(),
  }),
}))

vi.mock("better-auth/client/plugins", () => ({
  jwtClient: () => ({}),
  organizationClient: () => ({}),
}))

function makeJwt(expiresAt: number) {
  const payload = btoa(JSON.stringify({ exp: Math.floor(expiresAt / 1000) }))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "")

  return `header.${payload}.signature`
}

async function loadAuthClient() {
  vi.resetModules()
  return import("@/lib/auth-client")
}

describe("getBearerToken", () => {
  beforeEach(() => {
    betterAuthMocks.fetch.mockReset()
  })

  test("caches fresh JWTs until they near expiry", async () => {
    const token = makeJwt(Date.now() + 120_000)
    betterAuthMocks.fetch.mockResolvedValue({ data: { token }, error: null })
    const { getBearerToken } = await loadAuthClient()

    await expect(getBearerToken()).resolves.toBe(token)
    await expect(getBearerToken()).resolves.toBe(token)

    expect(betterAuthMocks.fetch).toHaveBeenCalledTimes(1)
  })

  test("clearBearerToken forces the next call to refetch", async () => {
    const firstToken = makeJwt(Date.now() + 120_000)
    const secondToken = makeJwt(Date.now() + 180_000)
    betterAuthMocks.fetch
      .mockResolvedValueOnce({ data: { token: firstToken }, error: null })
      .mockResolvedValueOnce({ data: { token: secondToken }, error: null })
    const { clearBearerToken, getBearerToken } = await loadAuthClient()

    await expect(getBearerToken()).resolves.toBe(firstToken)
    clearBearerToken()
    await expect(getBearerToken()).resolves.toBe(secondToken)

    expect(betterAuthMocks.fetch).toHaveBeenCalledTimes(2)
  })
})
