"use client"

import { organizationClient, jwtClient } from "better-auth/client/plugins"
import { createAuthClient } from "better-auth/react"

const authClient = createAuthClient({
  baseURL: process.env.NEXT_PUBLIC_AUTH_URL,
  plugins: [organizationClient(), jwtClient()],
})

async function getBearerToken() {
  try {
    const response = await authClient.$fetch<{ token: string }>("/token")

    if (response.error) {
      return null
    }

    return response.data.token
  } catch {
    return null
  }
}

export { authClient, getBearerToken }
