"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { QueryClient } from "@tanstack/react-query"

import { authClient } from "@/lib/auth-client"
import { queryKeys } from "@/lib/query-keys"

import type { Household, HouseholdFormValues, MemberRole } from "../schemas"

async function unwrap<T>(
  promise: Promise<{ data: unknown; error: { message?: string } | null }>,
): Promise<T> {
  const { data, error } = await promise
  if (error) {
    throw new Error(error.message || "Something went wrong. Please try again.")
  }
  return data as T
}

function invalidateMembers(queryClient: QueryClient, householdId: string) {
  queryClient.invalidateQueries({ queryKey: queryKeys.householdMembers(householdId) })
}

function invalidateInvitations(queryClient: QueryClient, householdId: string) {
  queryClient.invalidateQueries({
    queryKey: queryKeys.householdInvitations(householdId),
  })
}

function useCreateHousehold() {
  return useMutation({
    mutationFn: (data: HouseholdFormValues) =>
      unwrap<Household>(authClient.organization.create(data)),
  })
}

function useInviteMember(householdId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { email: string; role: MemberRole }) =>
      unwrap(
        authClient.organization.inviteMember({
          ...data,
          organizationId: householdId,
        }),
      ),
    onSuccess: () => invalidateInvitations(queryClient, householdId),
  })
}

function useCancelInvitation(householdId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (invitationId: string) =>
      unwrap(authClient.organization.cancelInvitation({ invitationId })),
    onSuccess: () => invalidateInvitations(queryClient, householdId),
  })
}

function useAcceptInvitation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (invitationId: string) =>
      unwrap(authClient.organization.acceptInvitation({ invitationId })),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.userInvitations() })
    },
  })
}

function useRejectInvitation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (invitationId: string) =>
      unwrap(authClient.organization.rejectInvitation({ invitationId })),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.userInvitations() })
    },
  })
}

function useUpdateMemberRole(householdId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { memberId: string; role: MemberRole }) =>
      unwrap(
        authClient.organization.updateMemberRole({
          ...data,
          organizationId: householdId,
        }),
      ),
    onSuccess: () => invalidateMembers(queryClient, householdId),
  })
}

function useRemoveMember(householdId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (memberIdOrEmail: string) =>
      unwrap(
        authClient.organization.removeMember({
          memberIdOrEmail,
          organizationId: householdId,
        }),
      ),
    onSuccess: () => invalidateMembers(queryClient, householdId),
  })
}

function useLeaveHousehold(householdId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () =>
      unwrap(authClient.organization.leave({ organizationId: householdId })),
    onSuccess: () => invalidateMembers(queryClient, householdId),
  })
}

export {
  useCreateHousehold,
  useInviteMember,
  useCancelInvitation,
  useAcceptInvitation,
  useRejectInvitation,
  useUpdateMemberRole,
  useRemoveMember,
  useLeaveHousehold,
}
