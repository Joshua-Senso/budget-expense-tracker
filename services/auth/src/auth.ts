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
      // Only trust Google, which guarantees verified email ownership before
      // returning the identity. GitHub and Discord report emailVerified too, so
      // verified users still auto-link via the default gate — trusting them here
      // would additionally link unverified-email identities and open an
      // account-takeover vector.
      trustedProviders: ["google"],
    },
  },
  advanced: {
    database: {
      generateId: "uuid",
    },
  },
})
