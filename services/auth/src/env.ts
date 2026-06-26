const requiredEnv = ["DATABASE_URL", "BETTER_AUTH_SECRET", "BETTER_AUTH_URL"] as const

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

export const env = {
  databaseUrl: readRequiredEnv("DATABASE_URL"),
  secret: readRequiredEnv("BETTER_AUTH_SECRET"),
  baseUrl: readRequiredEnv("BETTER_AUTH_URL"),
  jwtAudience: process.env.BETTER_AUTH_JWT_AUDIENCE ?? "expense-api",
  trustedOrigins: readTrustedOrigins(),
}
