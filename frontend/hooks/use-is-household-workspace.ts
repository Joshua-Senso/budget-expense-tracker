"use client"

import { useWorkspaceStore } from "@/stores/workspace-store"

function useIsHouseholdWorkspace() {
  return useWorkspaceStore((state) => state.activeWorkspaceScope === "household")
}

export { useIsHouseholdWorkspace }
