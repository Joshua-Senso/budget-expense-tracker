"use client"

import { getBearerToken } from "@/lib/auth-client"

type ApiRequestOptions = Omit<RequestInit, "body"> & {
  body?: BodyInit | Record<string, unknown> | null
}

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL

function shouldSerializeJsonBody(body: ApiRequestOptions["body"]) {
  return (
    body !== null &&
    typeof body === "object" &&
    !(body instanceof FormData) &&
    !(body instanceof URLSearchParams) &&
    !(body instanceof Blob) &&
    !(body instanceof ArrayBuffer) &&
    !(body instanceof ReadableStream)
  )
}

function buildApiUrl(path: string) {
  if (!apiBaseUrl) {
    throw new Error("NEXT_PUBLIC_API_URL is required")
  }

  return new URL(path, apiBaseUrl).toString()
}

async function apiFetch<T>(path: string, options: ApiRequestOptions = {}) {
  const headers = new Headers(options.headers)
  const token = await getBearerToken()

  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  let body: BodyInit | null | undefined
  if (shouldSerializeJsonBody(options.body)) {
    headers.set("Content-Type", "application/json")
    body = JSON.stringify(options.body)
  } else {
    body = options.body as BodyInit | null | undefined
  }

  const response = await fetch(buildApiUrl(path), {
    ...options,
    headers,
    body,
  })

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }

  if (response.status === 204) {
    return null as T
  }

  return (await response.json()) as T
}

export { apiFetch }
export type { ApiRequestOptions }
