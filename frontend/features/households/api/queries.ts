"use client"

import { useQuery } from "@tanstack/react-query"

import { authClient } from "@/lib/auth-client"
import { queryKeys } from "@/lib/query-keys"

import type { Household, Invitation, Member, MemberRole } from "../schemas"

function useHouseholds() {
  const { data, error, isPending, refetch } = authClient.useListOrganizations()

  return {
    households: (data ?? null) as Household[] | null,
    error,
    isPending,
    refetch,
  }
}

async function unwrapOrThrow<T>(
  promise: Promise<{ data: unknown; error: { message?: string } | null }>,
): Promise<T> {
  const { data, error } = await promise
  if (error) {
    throw new Error(error.message || "Failed to load. Please try again.")
  }
  return data as T
}

function useHouseholdMembers(householdId: string | null) {
  return useQuery({
    queryKey: queryKeys.householdMembers(householdId ?? ""),
    queryFn: () =>
      unwrapOrThrow<{ members: Member[]; total: number }>(
        authClient.organization.listMembers({
          query: { organizationId: householdId! },
        }),
      ),
    enabled: !!householdId,
  })
}

function useHouseholdInvitations(householdId: string | null) {
  return useQuery({
    queryKey: queryKeys.householdInvitations(householdId ?? ""),
    queryFn: () =>
      unwrapOrThrow<Invitation[]>(
        authClient.organization.listInvitations({
          query: { organizationId: householdId! },
        }),
      ),
    enabled: !!householdId,
  })
}

function useMyHouseholdRole(householdId: string | null): MemberRole | null {
  const { data } = useHouseholdMembers(householdId)
  const { data: session } = authClient.useSession()

  return (
    data?.members.find((member) => member.userId === session?.user.id)?.role ?? null
  )
}

function useUserInvitations() {
  return useQuery({
    queryKey: queryKeys.userInvitations(),
    queryFn: () =>
      unwrapOrThrow<
        (Invitation & { organizationName: string; organizationSlug: string })[]
      >(authClient.organization.listUserInvitations()),
  })
}

export {
  useHouseholds,
  useHouseholdMembers,
  useHouseholdInvitations,
  useMyHouseholdRole,
  useUserInvitations,
}
