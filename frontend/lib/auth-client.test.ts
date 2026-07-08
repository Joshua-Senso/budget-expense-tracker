import { afterEach, beforeEach, describe, expect, test, vi } from "vitest"

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
  inferAdditionalFields: () => ({}),
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
    vi.spyOn(console, "error").mockImplementation(() => {})
  })

  afterEach(() => {
    vi.restoreAllMocks()
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

  test("logs Better Auth errors before returning null", async () => {
    betterAuthMocks.fetch.mockResolvedValue({
      data: null,
      error: { message: "Not found", status: 404 },
    })
    const { getBearerToken } = await loadAuthClient()

    await expect(getBearerToken()).resolves.toBeNull()

    expect(console.error).toHaveBeenCalledWith(
      "auth: failed to fetch bearer token",
      { message: "Not found", status: 404 },
    )
  })

  test("logs malformed token responses before returning null", async () => {
    betterAuthMocks.fetch.mockResolvedValue({ data: {}, error: null })
    const { getBearerToken } = await loadAuthClient()

    await expect(getBearerToken()).resolves.toBeNull()

    expect(console.error).toHaveBeenCalledWith(
      "auth: bearer token response was malformed",
      {},
    )
  })

  test("logs thrown token request errors before returning null", async () => {
    const error = new Error("network failed")
    betterAuthMocks.fetch.mockRejectedValue(error)
    const { getBearerToken } = await loadAuthClient()

    await expect(getBearerToken()).resolves.toBeNull()

    expect(console.error).toHaveBeenCalledWith("auth: token request threw", error)
  })
})
