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
  socialProviders: {
    ...(env.google ? { google: env.google } : {}),
    ...(env.github ? { github: env.github } : {}),
    ...(env.discord ? { discord: env.discord } : {}),
  },
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
  account: {
    accountLinking: {
      // All three providers are trusted so implicit linking fires on email match
      // even when the provider doesn't return emailVerified: true (e.g. GitHub,
      // Discord). This keeps user_id stable across linked providers.
      trustedProviders: ["google", "github", "discord"],
    },
  },
  advanced: {
    database: {
      generateId: "uuid",
    },
  },
})
