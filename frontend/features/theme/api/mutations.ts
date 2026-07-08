"use client"

import { useMutation } from "@tanstack/react-query"

import { authClient } from "@/lib/auth-client"
import { useWorkspaceStore } from "@/stores/workspace-store"

import type { Theme } from "../schemas"

async function unwrap<T>(
  promise: Promise<{ data: unknown; error: { message?: string } | null }>,
): Promise<T> {
  const { data, error } = await promise
  if (error) {
    throw new Error(error.message || "Couldn't update the theme. Please try again.")
  }
  return data as T
}

// No manual query invalidation: Better Auth's client already refreshes
// `useListOrganizations()` on `/organization/update` and the session on
// `/update-user` (same reason useCreateHousehold has no onSuccess handler).
function useSetWorkspaceTheme() {
  const activeWorkspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)

  return useMutation({
    mutationFn: (theme: Theme) =>
      activeWorkspaceId
        ? unwrap(
            authClient.organization.update({
              organizationId: activeWorkspaceId,
              data: { theme },
            }),
          )
        : unwrap(authClient.updateUser({ theme })),
  })
}

export { useSetWorkspaceTheme }
