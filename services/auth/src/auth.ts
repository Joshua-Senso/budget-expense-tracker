import { betterAuth } from "better-auth"
import { jwt, organization } from "better-auth/plugins"
import { Pool } from "pg"

import { env } from "./env"

export const authTables = {
  user: "users",
  session: "sessions",
  account: "accounts",
  verification: "verifications",
  jwks: "jwks",
  organization: "organizations",
  member: "members",
  invitation: "invitations",
} as const

export const auth = betterAuth({
  appName: "Expense Tracker",
  basePath: "/api/auth",
  database: new Pool({
    connectionString: env.databaseUrl,
  }),
  secret: env.secret,
  baseURL: env.baseUrl,
  trustedOrigins: env.trustedOrigins,
  user: {
    modelName: authTables.user,
  },
  session: {
    modelName: authTables.session,
  },
  account: {
    modelName: authTables.account,
  },
  verification: {
    modelName: authTables.verification,
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
      schema: {
        organization: {
          modelName: authTables.organization,
        },
        member: {
          modelName: authTables.member,
        },
        invitation: {
          modelName: authTables.invitation,
        },
      },
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
