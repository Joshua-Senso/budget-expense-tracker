import { Hono } from "hono"
import { cors } from "hono/cors"

import { auth } from "./auth"
import { env } from "./env"

const app = new Hono()

app.get("/health", (c) => {
  return c.json({ status: "ok" })
})

app.use(
  "/api/auth/*",
  cors({
    origin: env.trustedOrigins,
    allowMethods: ["GET", "POST", "OPTIONS"],
    allowHeaders: ["Content-Type", "Authorization"],
    credentials: true,
  }),
)

app.all("/api/auth/*", (c) => {
  return auth.handler(c.req.raw)
})

export default {
  port: Number(process.env.PORT ?? 4000),
  fetch: app.fetch,
}
