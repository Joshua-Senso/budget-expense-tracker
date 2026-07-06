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
  const { households, isPending, error } = useHouseholds()
  const activeWorkspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  const setActiveWorkspace = useWorkspaceStore((state) => state.setActiveWorkspace)

  React.useEffect(() => {
    // Only clear a persisted selection once we've positively confirmed (a
    // successful load) that the household is gone. While still loading, or
    // if the fetch failed, `households` reads as null the same way an empty
    // list would -- treating that as "not a member anymore" would silently
    // drop the user to Personal (and misroute their next create) on every
    // transient network hiccup, not just a real removal.
    if (isPending || error) return

    if (
      activeWorkspaceId &&
      !(households ?? []).some((household) => household.id === activeWorkspaceId)
    ) {
      setActiveWorkspace({ id: null })
    }
  }, [activeWorkspaceId, households, isPending, error, setActiveWorkspace])

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
