"use client"

import { useState } from "react"

import { Button } from "@/components/ui/button"

import { useHouseholds, useUserInvitations } from "../api/queries"
import { useAcceptInvitation, useRejectInvitation } from "../api/mutations"

function ReceivedInvitations() {
  const { data, isLoading, isError, error: loadError } = useUserInvitations()
  const { refetch: refetchHouseholds } = useHouseholds()
  const acceptInvitation = useAcceptInvitation()
  const rejectInvitation = useRejectInvitation()
  const [error, setError] = useState<string | null>(null)
  const [pendingId, setPendingId] = useState<string | null>(null)

  const pending = (data ?? []).filter((invitation) => invitation.status === "pending")

  async function handleAccept(invitationId: string) {
    setError(null)
    setPendingId(invitationId)
    try {
      await acceptInvitation.mutateAsync(invitationId)
      refetchHouseholds()
    } catch {
      setError("Could not accept invitation. It may have expired.")
    } finally {
      setPendingId(null)
    }
  }

  async function handleReject(invitationId: string) {
    setError(null)
    setPendingId(invitationId)
    try {
      await rejectInvitation.mutateAsync(invitationId)
    } catch {
      setError("Could not decline invitation. Please try again.")
    } finally {
      setPendingId(null)
    }
  }

  if (isLoading) {
    return null
  }

  if (isError) {
    return (
      <p className="text-sm text-destructive" role="alert">
        {loadError instanceof Error
          ? loadError.message
          : "Could not load invitations for you."}
      </p>
    )
  }

  if (pending.length === 0) {
    return null
  }

  return (
    <section className="flex flex-col gap-3 rounded-2xl border bg-card p-4">
      <h2 className="text-sm font-semibold">Invitations for you</h2>
      <ul className="flex flex-col gap-2">
        {pending.map((invitation) => (
          <li
            key={invitation.id}
            className="flex items-center gap-3 rounded-xl border bg-background px-3 py-2"
          >
            <div className="min-w-0 flex-1">
              <span className="truncate text-sm font-medium">
                {invitation.organizationName}
              </span>
              <span className="ml-2 text-xs capitalize text-muted-foreground">
                as {invitation.role}
              </span>
            </div>
            <Button
              variant="outline"
              size="sm"
              disabled={pendingId === invitation.id}
              onClick={() => handleReject(invitation.id)}
            >
              Decline
            </Button>
            <Button
              size="sm"
              disabled={pendingId === invitation.id}
              onClick={() => handleAccept(invitation.id)}
            >
              Accept
            </Button>
          </li>
        ))}
      </ul>
      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}
    </section>
  )
}

export { ReceivedInvitations }
