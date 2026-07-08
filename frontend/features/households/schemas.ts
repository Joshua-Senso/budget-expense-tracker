import { z } from "zod"

type Household = {
  id: string
  name: string
  slug: string
  theme: string
}

const slugRegex = /^[a-z0-9-]+$/

const householdSchema = z.object({
  name: z.string().trim().min(1, "Name is required").max(100),
  slug: z
    .string()
    .trim()
    .min(1, "Slug is required")
    .max(50)
    .regex(slugRegex, "Lowercase letters, numbers, and hyphens only"),
})

type HouseholdFormValues = z.infer<typeof householdSchema>

const MEMBER_ROLES = ["owner", "member"] as const
type MemberRole = (typeof MEMBER_ROLES)[number]

type Member = {
  id: string
  organizationId: string
  userId: string
  role: MemberRole
  createdAt: string
  user: {
    id: string
    name: string
    email: string
    image?: string | null
  }
}

type InvitationStatus = "pending" | "accepted" | "rejected" | "canceled"

type Invitation = {
  id: string
  organizationId: string
  email: string
  role: MemberRole
  status: InvitationStatus
  inviterId: string
  expiresAt: string
  createdAt: string
}

const inviteMemberSchema = z.object({
  email: z.string().trim().min(1, "Email is required").email("Enter a valid email"),
  role: z.enum(MEMBER_ROLES),
})

type InviteMemberFormValues = z.infer<typeof inviteMemberSchema>

export { householdSchema, inviteMemberSchema, MEMBER_ROLES }
export type {
  Household,
  HouseholdFormValues,
  Member,
  MemberRole,
  Invitation,
  InvitationStatus,
  InviteMemberFormValues,
}
