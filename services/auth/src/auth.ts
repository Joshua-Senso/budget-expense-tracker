import { kyselyAdapter } from "@better-auth/kysely-adapter"
import { betterAuth } from "better-auth"
import { jwt, organization } from "better-auth/plugins"
import { Kysely, PostgresDialect } from "kysely"
import { Pool } from "pg"

import { env } from "./env"

// better-auth's automatic Pool -> Kysely adapter wiring drops `usePlural`, so
// the adapter must be built explicitly to actually query the plural tables
// (`users`, `sessions`, …) that the CLI migrations created.
const db = new Kysely({
  dialect: new PostgresDialect({
    pool: new Pool({ connectionString: env.databaseUrl }),
  }),
})

export const auth = betterAuth({
  appName: "Expense Tracker",
  basePath: "/api/auth",
  // better-auth's usePlural blindly appends "s" to every model name, which is
  // wrong for models that are already plural (e.g. "jwks" -> "jwkss"). Instead
  // of relying on it, map each model to its actual (already-plural) table name.
  database: kyselyAdapter(db, { type: "postgres" }),
  secret: env.secret,
  baseURL: env.baseUrl,
  trustedOrigins: env.trustedOrigins,
  user: { modelName: "users" },
  session: { modelName: "sessions" },
  verification: { modelName: "verifications" },
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
      schema: {
        organization: { modelName: "organizations" },
        member: { modelName: "members" },
        invitation: { modelName: "invitations" },
      },
    }),
  ],
  account: {
    modelName: "accounts",
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
