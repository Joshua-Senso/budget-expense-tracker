import { describe, expect, test } from "bun:test"

process.env.DATABASE_URL = "postgresql://expense:expense@localhost:5432/expense"
process.env.BETTER_AUTH_URL = "http://localhost:4000"
process.env.BETTER_AUTH_SECRET = "test-auth-secret-placeholder-32chars"
process.env.BETTER_AUTH_JWT_AUDIENCE = "expense-api"
process.env.BETTER_AUTH_TRUSTED_ORIGINS = "http://localhost:3000"

describe("auth config", () => {
  test("uses the service base path and trusted frontend origin", async () => {
    const { auth } = await import("../src/auth")

    expect(auth.options.basePath).toBe("/api/auth")
    expect(auth.options.baseURL).toBe("http://localhost:4000")
    expect(auth.options.trustedOrigins).toEqual(["http://localhost:3000"])
  })

  test("configures JWT issuer, audience, and canonical subject", async () => {
    const { auth } = await import("../src/auth")
    const jwtPlugin = auth.options.plugins?.find((plugin) => plugin.id === "jwt")
    const subject = await jwtPlugin?.options?.jwt?.getSubject?.({
      user: { id: "user-id" },
      session: {},
    })

    expect(jwtPlugin?.options?.jwt?.issuer).toBe("http://localhost:4000")
    expect(jwtPlugin?.options?.jwt?.audience).toBe("expense-api")
    expect(subject).toBe("user-id")
  })

  test("keeps Better Auth-owned tables plural", async () => {
    const { auth } = await import("../src/auth")

    expect(auth.options.usePlural).toBe(true)
  })

  test("enables JWT/JWKS and organization plugins", async () => {
    const { auth } = await import("../src/auth")
    const pluginIds = auth.options.plugins?.map((plugin) => plugin.id)

    expect(pluginIds).toContain("jwt")
    expect(pluginIds).toContain("organization")
  })
})

describe("account linking", () => {
  test("only google is a trusted provider — github and discord rely on emailVerified", async () => {
    const { auth } = await import("../src/auth")
    const trusted = auth.options.account?.accountLinking?.trustedProviders as string[] | undefined

    expect(trusted).toContain("google")
    expect(trusted).not.toContain("github")
    expect(trusted).not.toContain("discord")
  })
})

describe("social providers", () => {
  test("no providers are enabled when OAuth env vars are absent", async () => {
    const { auth } = await import("../src/auth")
    const providers = auth.options.socialProviders ?? {}

    expect(Object.keys(providers)).toHaveLength(0)
  })
})

describe("auth server", () => {
  test("GET / returns not found", async () => {
    const server = await import("../src/server")

    const res = await server.default.fetch(new Request("http://localhost/"))

    expect(res.status).toBe(404)
  })

  test("GET /health returns ok", async () => {
    const server = await import("../src/server")

    const res = await server.default.fetch(new Request("http://localhost/health"))

    expect(res.status).toBe(200)
    expect(await res.json()).toEqual({ status: "ok" })
  })

  test("mounts Better Auth routes under /api/auth", async () => {
    const server = await import("../src/server")

    const res = await server.default.fetch(new Request("http://localhost/api/auth/ok"))

    expect(res.status).toBe(200)
  })
})
