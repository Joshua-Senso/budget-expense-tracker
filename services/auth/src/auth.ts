import { betterAuth } from "better-auth"
import { jwt, organization } from "better-auth/plugins"
import { Pool } from "pg"

import { env } from "./env"

export const auth = betterAuth({
  appName: "Expense Tracker",
  basePath: "/api/auth",
  database: new Pool({
    connectionString: env.databaseUrl,
  }),
  secret: env.secret,
  baseURL: env.baseUrl,
  trustedOrigins: env.trustedOrigins,
  usePlural: true,
  plugins: [
    jwt({
      jwks: {
        keyPairConfig: {
          alg: "RS256",
          modulusLength: 2048,
        },
      },
      jwt: {
        issuer: env.baseUrl,
        audience: env.jwtAudience,
        getSubject: ({ user }) => user.id,
      },
    }),
    organization({
      teams: {
        enabled: false,
      },
    }),
  ],
  advanced: {
    database: {
      generateId: "uuid",
    },
  },
})
