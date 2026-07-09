"use client"

import {
  organizationClient,
  jwtClient,
  inferAdditionalFields,
} from "better-auth/client/plugins"
import { createAuthClient } from "better-auth/react"

const authClient = createAuthClient({
  baseURL: process.env.NEXT_PUBLIC_AUTH_URL,
  plugins: [
    // Frontend and services/auth are separate deployables (no shared pnpm
    // workspace), so additionalFields are typed here via an inline schema
    // literal rather than `typeof auth` -- keep these in sync with the
    // matching fields in services/auth/src/auth.ts.
    organizationClient({
      schema: {
        organization: {
          additionalFields: { theme: { type: "string", required: false } as const },
        },
      },
    }),
    inferAdditionalFields({
      user: { theme: { type: "string", required: false } as const },
    }),
    jwtClient(),
  ],
})

const tokenPath = "/token"

type CachedBearerToken = {
  token: string
  expiresAt: number
}

let cachedBearerToken: CachedBearerToken | null = null
let pendingBearerToken: Promise<string | null> | null = null
// Bumped by clearBearerToken() so a fetch that was already in flight at
// sign-out time can't repopulate the cache once it resolves afterward --
// otherwise a fast sign-in by a second user on the same tab could still
// inherit the previous user's token.
let tokenGeneration = 0

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
  pendingBearerToken = null
  tokenGeneration += 1
}

async function fetchBearerToken() {
  const generation = tokenGeneration

  try {
    // Better Auth is mounted at /api/auth, so this should resolve to /api/auth/token.
    const response = await authClient.$fetch<{ token: string }>(tokenPath)

    if (response.error) {
      console.error("auth: failed to fetch bearer token", response.error)
      return null
    }

    const token = response.data?.token
    if (!token) {
      console.error("auth: bearer token response was malformed", response.data)
      return null
    }

    const expiresAt = getTokenExpiry(token)

    // A clearBearerToken() call while this request was in flight must not
    // let it repopulate the cache with a token issued before the clear.
    if (expiresAt > Date.now() && generation === tokenGeneration) {
      cachedBearerToken = { token, expiresAt }
    }

    return token
  } catch (error) {
    console.error("auth: token request threw", error)
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
