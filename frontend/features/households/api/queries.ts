"use client"

import { authClient } from "@/lib/auth-client"

import type { Household } from "../schemas"

function useHouseholds() {
  const { data, error, isPending } = authClient.useListOrganizations()

  return { households: (data ?? null) as Household[] | null, error, isPending }
}

export { useHouseholds }
