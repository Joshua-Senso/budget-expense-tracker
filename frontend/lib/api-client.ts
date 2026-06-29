"use client"

import { clearBearerToken, getBearerToken } from "@/lib/auth-client"

type ApiRequestOptions = Omit<RequestInit, "body"> & {
  body?: BodyInit | Record<string, unknown> | null
}

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL

class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly body: unknown,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

function shouldSerializeJsonBody(body: ApiRequestOptions["body"]) {
  return (
    body !== null &&
    typeof body === "object" &&
    !(body instanceof FormData) &&
    !(body instanceof URLSearchParams) &&
    !(body instanceof Blob) &&
    !(body instanceof ArrayBuffer) &&
    !ArrayBuffer.isView(body) &&
    !(body instanceof ReadableStream)
  )
}

function buildApiUrl(path: string) {
  if (!apiBaseUrl) {
    throw new Error("NEXT_PUBLIC_API_URL is required")
  }

  const base = apiBaseUrl.replace(/\/+$/, "")
  const cleanPath = path.replace(/^\/+/, "")

  return `${base}/${cleanPath}`
}

async function parseResponseBody(response: Response) {
  const contentType = response.headers.get("Content-Type")
  if (contentType?.includes("application/json")) {
    try {
      return await response.json()
    } catch {
      return null
    }
  }

  const text = await response.text()
  return text || null
}

function normalizeBody(body: ApiRequestOptions["body"], headers: Headers) {
  if (shouldSerializeJsonBody(body)) {
    headers.set("Content-Type", "application/json")
    return JSON.stringify(body)
  }

  return body as BodyInit | null | undefined
}

async function fetchWithAuth(path: string, options: ApiRequestOptions) {
  const headers = new Headers(options.headers)
  const token = await getBearerToken()

  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  return {
    response: await fetch(buildApiUrl(path), {
      ...options,
      headers,
      body: normalizeBody(options.body, headers),
    }),
    token,
  }
}

async function apiFetch<T>(path: string, options: ApiRequestOptions = {}) {
  const { response: firstResponse, token } = await fetchWithAuth(path, options)
  let response = firstResponse

  if (response.status === 401 && token) {
    clearBearerToken()
    response = (await fetchWithAuth(path, options)).response
  }

  if (!response.ok) {
    const body = await parseResponseBody(response)
    throw new ApiError(`API request failed: ${response.status}`, response.status, body)
  }

  if (response.status === 204) {
    return null as T
  }

  return (await parseResponseBody(response)) as T
}

export { ApiError, apiFetch }
export type { ApiRequestOptions }
