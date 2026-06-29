"use client"

import { organizationClient, jwtClient } from "better-auth/client/plugins"
import { createAuthClient } from "better-auth/react"

const authClient = createAuthClient({
  baseURL: process.env.NEXT_PUBLIC_AUTH_URL,
  plugins: [organizationClient(), jwtClient()],
})

type CachedBearerToken = {
  token: string
  expiresAt: number
}

let cachedBearerToken: CachedBearerToken | null = null
let pendingBearerToken: Promise<string | null> | null = null

function decodeJwtPayload(token: string) {
  const [, payload] = token.split(".")
  if (!payload) {
    return null
  }

  try {
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/")
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=")
    return JSON.parse(atob(padded)) as { exp?: unknown }
  } catch {
    return null
  }
}

function getTokenExpiry(token: string) {
  const payload = decodeJwtPayload(token)
  if (typeof payload?.exp !== "number") {
    return 0
  }

  return payload.exp * 1000
}

function isTokenFresh(token: CachedBearerToken) {
  return token.expiresAt > Date.now() + 30_000
}

function clearBearerToken() {
  cachedBearerToken = null
}

async function fetchBearerToken() {
  try {
    const response = await authClient.$fetch<{ token: string }>("/token")

    if (response.error) {
      return null
    }

    const token = response.data.token
    const expiresAt = getTokenExpiry(token)

    if (expiresAt > Date.now()) {
      cachedBearerToken = { token, expiresAt }
    }

    return token
  } catch {
    return null
  }
}

async function getBearerToken() {
  if (cachedBearerToken && isTokenFresh(cachedBearerToken)) {
    return cachedBearerToken.token
  }

  pendingBearerToken ??= fetchBearerToken().finally(() => {
    pendingBearerToken = null
  })

  return pendingBearerToken
}

export { authClient, clearBearerToken, getBearerToken }
