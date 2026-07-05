import { kyselyAdapter } from "@better-auth/kysely-adapter"
import { betterAuth } from "better-auth"
import { jwt, organization } from "better-auth/plugins"
import { memberAc, ownerAc } from "better-auth/plugins/organization/access"
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
      // Explicit even though it's the library default: a household's creator
      // must become its owner (PRD §9.5, §7.9).
      creatorRole: "owner",
      // Only owner/member for now (PRD §9.5 "additional roles such as admin
      // may be enabled later"); replaces the library default roles, which
      // otherwise also expose a near-owner-level "admin" role we don't want yet.
      roles: {
        owner: ownerAc,
        member: memberAc,
      },
      schema: {
        organization: {
          modelName: "organizations",
          // Household base currency + theme extend the organization record
          // instead of a separate table (PRD §9.5).
          additionalFields: {
            // `required: false` only means "optional as caller input" — the
            // column itself is NOT NULL with a DB default, and `defaultValue`
            // fills it in on create when the caller omits it. Do NOT use
            // `input: false` here: that excludes the field from BOTH the
            // create *and* update body schemas, which would make these
            // fields impossible to change later (needed by M7 base currency
            // and M8 theme switching).
            baseCurrency: { type: "string", required: false, defaultValue: "PHP" },
            theme: { type: "string", required: false, defaultValue: "dark" },
          },
        },
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
