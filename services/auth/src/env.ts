const requiredEnv = ["DATABASE_URL", "BETTER_AUTH_SECRET", "BETTER_AUTH_URL", "REDIS_URL"] as const

type RequiredEnv = (typeof requiredEnv)[number]

function readRequiredEnv(name: RequiredEnv): string {
  const value = process.env[name]

  if (!value) {
    throw new Error(`${name} is required`)
  }

  return value
}

function readTrustedOrigins(): string[] {
  return (process.env.BETTER_AUTH_TRUSTED_ORIGINS ?? process.env.FRONTEND_ORIGIN ?? "")
    .split(",")
    .map((origin) => origin.trim())
    .filter(Boolean)
}

function readOAuthProvider(idKey: string, secretKey: string) {
  const clientId = process.env[idKey]
  const clientSecret = process.env[secretKey]
  if (!clientId || !clientSecret) return undefined
  return { clientId, clientSecret }
}

function readBaseUrl(): string {
  const baseUrl = readRequiredEnv("BETTER_AUTH_URL")

  // Better Auth derives the `secure` cookie flag from this URL's scheme, so a
  // prod misconfiguration would silently degrade cookie security.
  if (process.env.NODE_ENV === "production" && !baseUrl.startsWith("https://")) {
    throw new Error("BETTER_AUTH_URL must use https:// when NODE_ENV=production")
  }

  return baseUrl
}

export const env = {
  databaseUrl: readRequiredEnv("DATABASE_URL"),
  secret: readRequiredEnv("BETTER_AUTH_SECRET"),
  baseUrl: readBaseUrl(),
  jwtAudience: process.env.BETTER_AUTH_JWT_AUDIENCE ?? "expense-api",
  trustedOrigins: readTrustedOrigins(),
  redisUrl: readRequiredEnv("REDIS_URL"),
  google: readOAuthProvider("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"),
  github: readOAuthProvider("GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET"),
  discord: readOAuthProvider("DISCORD_CLIENT_ID", "DISCORD_CLIENT_SECRET"),
}
