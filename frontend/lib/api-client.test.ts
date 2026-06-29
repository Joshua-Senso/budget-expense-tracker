import { beforeEach, describe, expect, test, vi } from "vitest"

const authMocks = vi.hoisted(() => ({
  clearBearerToken: vi.fn(),
  getBearerToken: vi.fn(),
}))

vi.mock("@/lib/auth-client", () => authMocks)

async function loadClient() {
  vi.resetModules()
  vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.example.com/api")
  return import("@/lib/api-client")
}

function jsonResponse(body: unknown, init?: ResponseInit) {
  return new Response(JSON.stringify(body), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  })
}

describe("apiFetch", () => {
  beforeEach(() => {
    authMocks.clearBearerToken.mockReset()
    authMocks.getBearerToken.mockReset()
    vi.unstubAllGlobals()
    vi.unstubAllEnvs()
  })

  test("attaches bearer tokens and preserves API base paths", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }))
    vi.stubGlobal("fetch", fetchMock)
    authMocks.getBearerToken.mockResolvedValue("jwt-token")
    const { apiFetch } = await loadClient()

    await apiFetch("/expenses")

    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.example.com/api/expenses",
      expect.objectContaining({
        headers: expect.any(Headers),
      }),
    )
    const [, init] = fetchMock.mock.calls[0]
    expect((init.headers as Headers).get("Authorization")).toBe(
      "Bearer jwt-token",
    )
  })

  test("serializes plain object bodies as JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ id: "expense-1" }))
    vi.stubGlobal("fetch", fetchMock)
    authMocks.getBearerToken.mockResolvedValue(null)
    const { apiFetch } = await loadClient()

    await apiFetch("expenses", {
      method: "POST",
      body: { amount: 100 },
    })

    const [, init] = fetchMock.mock.calls[0]
    expect((init.headers as Headers).get("Content-Type")).toBe(
      "application/json",
    )
    expect(init.body).toBe(JSON.stringify({ amount: 100 }))
  })

  test("preserves form and binary bodies", async () => {
    const fetchMock = vi.fn().mockImplementation(() => jsonResponse({ ok: true }))
    vi.stubGlobal("fetch", fetchMock)
    authMocks.getBearerToken.mockResolvedValue(null)
    const { apiFetch } = await loadClient()
    const formData = new FormData()
    const binaryBody = new Uint8Array([1, 2, 3])

    await apiFetch("/receipts", { method: "POST", body: formData })
    await apiFetch("/receipts/raw", { method: "POST", body: binaryBody })

    expect(fetchMock.mock.calls[0][1].body).toBe(formData)
    expect(fetchMock.mock.calls[0][1].headers.get("Content-Type")).toBeNull()
    expect(fetchMock.mock.calls[1][1].body).toBe(binaryBody)
    expect(fetchMock.mock.calls[1][1].headers.get("Content-Type")).toBeNull()
  })

  test("throws typed errors with response status and body", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse({ detail: "Invalid" }, { status: 422 }))
    vi.stubGlobal("fetch", fetchMock)
    authMocks.getBearerToken.mockResolvedValue(null)
    const { ApiError, apiFetch } = await loadClient()

    const promise = apiFetch("/expenses")

    await expect(promise).rejects.toMatchObject({
      body: { detail: "Invalid" },
      status: 422,
    })
    await expect(promise).rejects.toBeInstanceOf(ApiError)
  })

  test("clears cached tokens and retries once after 401", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ detail: "Unauthorized" }, { status: 401 }))
      .mockResolvedValueOnce(jsonResponse({ user_id: "user-1" }))
    vi.stubGlobal("fetch", fetchMock)
    authMocks.getBearerToken
      .mockResolvedValueOnce("stale-token")
      .mockResolvedValueOnce("fresh-token")
    const { apiFetch } = await loadClient()

    await expect(apiFetch("/me")).resolves.toEqual({ user_id: "user-1" })

    expect(authMocks.clearBearerToken).toHaveBeenCalledTimes(1)
    expect(fetchMock.mock.calls[0][1].headers.get("Authorization")).toBe(
      "Bearer stale-token",
    )
    expect(fetchMock.mock.calls[1][1].headers.get("Authorization")).toBe(
      "Bearer fresh-token",
    )
  })
})
