create table "users" ("id" uuid default pg_catalog.gen_random_uuid() not null primary key, "name" text not null, "email" text not null unique, "emailVerified" boolean not null, "image" text, "createdAt" timestamptz default CURRENT_TIMESTAMP not null, "updatedAt" timestamptz default CURRENT_TIMESTAMP not null);

create table "sessions" ("id" uuid default pg_catalog.gen_random_uuid() not null primary key, "expiresAt" timestamptz not null, "token" text not null unique, "createdAt" timestamptz default CURRENT_TIMESTAMP not null, "updatedAt" timestamptz not null, "ipAddress" text, "userAgent" text, "userId" uuid not null references "users" ("id") on delete cascade, "activeOrganizationId" text);

create table "accounts" ("id" uuid default pg_catalog.gen_random_uuid() not null primary key, "accountId" text not null, "providerId" text not null, "userId" uuid not null references "users" ("id") on delete cascade, "accessToken" text, "refreshToken" text, "idToken" text, "accessTokenExpiresAt" timestamptz, "refreshTokenExpiresAt" timestamptz, "scope" text, "password" text, "createdAt" timestamptz default CURRENT_TIMESTAMP not null, "updatedAt" timestamptz not null);

create table "verifications" ("id" uuid default pg_catalog.gen_random_uuid() not null primary key, "identifier" text not null, "value" text not null, "expiresAt" timestamptz not null, "createdAt" timestamptz default CURRENT_TIMESTAMP not null, "updatedAt" timestamptz default CURRENT_TIMESTAMP not null);

create table "jwks" ("id" uuid default pg_catalog.gen_random_uuid() not null primary key, "publicKey" text not null, "privateKey" text not null, "createdAt" timestamptz not null, "expiresAt" timestamptz);

create table "organizations" ("id" uuid default pg_catalog.gen_random_uuid() not null primary key, "name" text not null, "slug" text not null unique, "logo" text, "createdAt" timestamptz not null, "metadata" text);

create table "members" ("id" uuid default pg_catalog.gen_random_uuid() not null primary key, "organizationId" uuid not null references "organizations" ("id") on delete cascade, "userId" uuid not null references "users" ("id") on delete cascade, "role" text not null, "createdAt" timestamptz not null);

create table "invitations" ("id" uuid default pg_catalog.gen_random_uuid() not null primary key, "organizationId" uuid not null references "organizations" ("id") on delete cascade, "email" text not null, "role" text, "status" text not null, "expiresAt" timestamptz not null, "createdAt" timestamptz default CURRENT_TIMESTAMP not null, "inviterId" uuid not null references "users" ("id") on delete cascade);

create index "sessions_userId_idx" on "sessions" ("userId");

create index "accounts_userId_idx" on "accounts" ("userId");

create index "verifications_identifier_idx" on "verifications" ("identifier");

create unique index "organizations_slug_uidx" on "organizations" ("slug");

create index "members_organizationId_idx" on "members" ("organizationId");

create index "members_userId_idx" on "members" ("userId");

create index "invitations_organizationId_idx" on "invitations" ("organizationId");

create index "invitations_email_idx" on "invitations" ("email");