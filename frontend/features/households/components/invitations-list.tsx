"use client"

import { useState } from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ApiError } from "@/lib/api-client"

import { useHouseholdInvitations } from "../api/queries"
import { useCancelInvitation } from "../api/mutations"

function getCancelErrorMessage(err: unknown) {
  if (err instanceof ApiError && err.status === 404) {
    return "This invitation no longer exists. Refresh the page and try again."
  }

  return "Could not cancel invitation. Please try again."
}

function InvitationsList({ householdId }: { householdId: string }) {
  const { data, isLoading, isError } = useHouseholdInvitations(householdId)
  const cancelInvitation = useCancelInvitation(householdId)
  const [error, setError] = useState<string | null>(null)
  const [pendingId, setPendingId] = useState<string | null>(null)

  const pending = (data ?? []).filter((invitation) => invitation.status === "pending")

  async function handleCancel(invitationId: string) {
    setError(null)
    setPendingId(invitationId)
    try {
      await cancelInvitation.mutateAsync(invitationId)
    } catch (err) {
      setError(getCancelErrorMessage(err))
    } finally {
      setPendingId(null)
    }
  }

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading invitations…</p>
  }

  if (isError) {
    return (
      <p className="text-sm text-destructive" role="alert">
        Failed to load invitations.
      </p>
    )
  }

  if (pending.length === 0) {
    return <p className="text-sm text-muted-foreground">No pending invitations.</p>
  }

  return (
    <div className="flex flex-col gap-2">
      <ul className="flex flex-col gap-2">
        {pending.map((invitation) => (
          <li
            key={invitation.id}
            className="flex items-center gap-3 rounded-2xl border bg-card px-4 py-3"
          >
            <div className="min-w-0 flex-1">
              <span className="truncate text-sm font-medium">{invitation.email}</span>
            </div>
            <Badge variant="secondary" className="shrink-0 capitalize">
              {invitation.role}
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              className="shrink-0 text-destructive hover:text-destructive"
              disabled={pendingId === invitation.id}
              onClick={() => handleCancel(invitation.id)}
            >
              Cancel
            </Button>
          </li>
        ))}
      </ul>
      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}

export { InvitationsList }
