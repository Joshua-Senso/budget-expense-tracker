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

  test("maps every model to its actual (already-plural) table name", async () => {
    const { getAuthTables } = await import("better-auth/db")
    const { auth } = await import("../src/auth")
    const tables = getAuthTables(auth.options)

    expect(tables.user?.modelName).toBe("users")
    expect(tables.session?.modelName).toBe("sessions")
    expect(tables.account?.modelName).toBe("accounts")
    expect(tables.verification?.modelName).toBe("verifications")
    expect(tables.organization?.modelName).toBe("organizations")
    expect(tables.member?.modelName).toBe("members")
    expect(tables.invitation?.modelName).toBe("invitations")
    // "jwks" is already plural — must NOT become "jwkss".
    expect(tables.jwks?.modelName).toBe("jwks")
  })

  test("enables JWT/JWKS and organization plugins", async () => {
    const { auth } = await import("../src/auth")
    const pluginIds = auth.options.plugins?.map((plugin) => plugin.id)

    expect(pluginIds).toContain("jwt")
    expect(pluginIds).toContain("organization")
  })

  test("extends the user record with a personal-workspace theme instead of a new table", async () => {
    const { getAuthTables } = await import("better-auth/db")
    const { auth } = await import("../src/auth")
    const tables = getAuthTables(auth.options)

    expect(tables.user?.fields.theme).toMatchObject({
      type: "string",
      required: false,
      defaultValue: "dark",
    })
  })
})

describe("households (organization plugin)", () => {
  test("the household creator becomes its owner", async () => {
    const { auth } = await import("../src/auth")
    const orgPlugin = auth.options.plugins?.find((plugin) => plugin.id === "organization")

    expect(orgPlugin?.options?.creatorRole).toBe("owner")
  })

  test("extends the organization record with base currency + theme instead of a new table", async () => {
    const { getAuthTables } = await import("better-auth/db")
    const { auth } = await import("../src/auth")
    const tables = getAuthTables(auth.options)
    const fields = tables.organization?.fields ?? {}

    expect(fields.baseCurrency).toMatchObject({ type: "string", required: false, defaultValue: "PHP" })
    expect(fields.theme).toMatchObject({ type: "string", required: false, defaultValue: "dark" })
  })

  test("no role is offered beyond owner/member, but admin is still mapped (not omitted)", async () => {
    const { auth } = await import("../src/auth")
    const orgPlugin = auth.options.plugins?.find((plugin) => plugin.id === "organization")

    // "admin" must stay mapped: the library's invite/update-role validators
    // accept it as a role name regardless of this config, so omitting it here
    // would leave any member who ends up with that role with permissions that
    // resolve to `undefined` instead of a predictable, safe default.
    expect(Object.keys(orgPlugin?.options?.roles ?? {}).sort()).toEqual(["admin", "member", "owner"])
  })

  test("only the owner role can invite members and remove/manage membership", async () => {
    const { hasPermission } = await import("better-auth/plugins/organization")
    const { auth } = await import("../src/auth")
    const options = auth.options.plugins?.find((plugin) => plugin.id === "organization")?.options

    expect(await hasPermission({ role: "owner", options, permissions: { invitation: ["create"] } })).toBe(true)
    expect(await hasPermission({ role: "owner", options, permissions: { member: ["delete"] } })).toBe(true)
    expect(await hasPermission({ role: "member", options, permissions: { invitation: ["create"] } })).toBe(false)
    expect(await hasPermission({ role: "member", options, permissions: { member: ["delete"] } })).toBe(false)
  })

  test("a member row that somehow ends up with role \"admin\" resolves to member-level permissions, not undefined", async () => {
    const { hasPermission } = await import("better-auth/plugins/organization")
    const { auth } = await import("../src/auth")
    const options = auth.options.plugins?.find((plugin) => plugin.id === "organization")?.options

    expect(await hasPermission({ role: "admin", options, permissions: { invitation: ["create"] } })).toBe(false)
    expect(await hasPermission({ role: "admin", options, permissions: { member: ["delete"] } })).toBe(false)
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
