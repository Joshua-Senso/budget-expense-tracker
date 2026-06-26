import { Hono } from "hono"

import { auth } from "./auth"

const app = new Hono()

app.get("/health", (c) => {
  return c.json({ status: "ok" })
})

app.all("/api/auth/*", (c) => {
  return auth.handler(c.req.raw)
})

export default {
  port: Number(process.env.PORT ?? 4000),
  fetch: app.fetch,
}
