"use client"

import { authClient } from "@/lib/auth-client"
import { useHouseholds } from "@/features/households"
import { useWorkspaceStore } from "@/stores/workspace-store"

import { DEFAULT_THEME } from "../constants"
import { themeSchema, type Theme } from "../schemas"

function parseTheme(value: string | null | undefined): Theme {
  const result = themeSchema.safeParse(value)
  return result.success ? result.data : DEFAULT_THEME
}

// Built only on Better Auth's own hooks (never TanStack Query's `useQuery`):
// this is read from `WorkspaceThemeSync` in providers/theme-provider.tsx,
// which renders outside the QueryClientProvider subtree (see providers.tsx --
// ThemeProvider wraps QueryProvider, not the other way around).
function useWorkspaceTheme() {
  const activeWorkspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  const { data: session, isPending: sessionPending } = authClient.useSession()
  const { households, isPending: householdsPending } = useHouseholds()

  if (activeWorkspaceId === null) {
    return {
      theme: parseTheme(session?.user.theme),
      isPending: sessionPending,
      scope: "personal" as const,
      household: undefined,
    }
  }

  const household = households?.find((item) => item.id === activeWorkspaceId)

  return {
    theme: parseTheme(household?.theme),
    isPending: householdsPending,
    scope: "household" as const,
    household,
  }
}

export { useWorkspaceTheme }
