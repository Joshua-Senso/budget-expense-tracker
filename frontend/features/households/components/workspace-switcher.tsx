"use client"

import * as React from "react"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useWorkspaceStore } from "@/stores/workspace-store"

import { useHouseholds } from "../api/queries"

const PERSONAL_VALUE = "personal"

function WorkspaceSwitcher() {
  const { households, isPending } = useHouseholds()
  const activeWorkspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  const setActiveWorkspace = useWorkspaceStore((state) => state.setActiveWorkspace)

  React.useEffect(() => {
    // Wait for the list to settle before judging membership -- while it's
    // still loading, `households` and "fetch errored" are indistinguishable
    // (both read as null), so a stale selection must not be cleared yet, and
    // must not be trusted forever if the fetch keeps failing.
    if (isPending) return

    if (
      activeWorkspaceId &&
      !(households ?? []).some((household) => household.id === activeWorkspaceId)
    ) {
      setActiveWorkspace({ id: null })
    }
  }, [activeWorkspaceId, households, isPending, setActiveWorkspace])

  return (
    <Select
      value={activeWorkspaceId ?? PERSONAL_VALUE}
      onValueChange={(value) =>
        setActiveWorkspace({ id: value === PERSONAL_VALUE ? null : value })
      }
    >
      <SelectTrigger className="w-[180px]" size="sm" aria-label="Active workspace">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={PERSONAL_VALUE}>Personal</SelectItem>
        {households?.map((household) => (
          <SelectItem key={household.id} value={household.id}>
            {household.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

export { WorkspaceSwitcher }
