import { describe, expect, test } from "bun:test"

import server from "../src/index"

describe("auth server", () => {
  test("GET / returns hello", async () => {
    const res = await server.fetch(new Request("http://localhost/"))
    expect(res.status).toBe(200)
    expect(await res.text()).toBe("Hello Hono!")
  })
})
