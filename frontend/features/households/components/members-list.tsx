"use client"

import { useState } from "react"

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { authClient } from "@/lib/auth-client"

import { useHouseholdMembers, useHouseholds, useMyHouseholdRole } from "../api/queries"
import {
  useLeaveHousehold,
  useRemoveMember,
  useUpdateMemberRole,
} from "../api/mutations"
import type { Member, MemberRole } from "../schemas"

function genericErrorMessage(action: "remove" | "leave" | "update the role of") {
  return `Could not ${action} this member. Households must keep at least one owner.`
}

interface MemberRowProps {
  member: Member
  isSelf: boolean
  canManage: boolean
  onError: (message: string | null) => void
  onLeft: () => void
  updateRole: ReturnType<typeof useUpdateMemberRole>
  removeMember: ReturnType<typeof useRemoveMember>
  leaveHousehold: ReturnType<typeof useLeaveHousehold>
}

function MemberRow({
  member,
  isSelf,
  canManage,
  onError,
  onLeft,
  updateRole,
  removeMember,
  leaveHousehold,
}: MemberRowProps) {
  const [confirmOpen, setConfirmOpen] = useState(false)
  const isPending = updateRole.isPending || removeMember.isPending || leaveHousehold.isPending

  async function handleRoleChange(role: MemberRole) {
    onError(null)
    try {
      await updateRole.mutateAsync({ memberId: member.id, role })
    } catch {
      onError(genericErrorMessage("update the role of"))
    }
  }

  async function handleConfirm() {
    onError(null)
    try {
      if (isSelf) {
        await leaveHousehold.mutateAsync()
        onLeft()
      } else {
        await removeMember.mutateAsync(member.id)
      }
      setConfirmOpen(false)
    } catch {
      onError(genericErrorMessage(isSelf ? "leave" : "remove"))
    }
  }

  return (
    <li className="flex items-center gap-3 rounded-2xl border bg-card px-4 py-3">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm font-medium">{member.user.name}</span>
          {isSelf && (
            <Badge variant="outline" className="shrink-0">
              You
            </Badge>
          )}
        </div>
        <span className="truncate text-xs text-muted-foreground">
          {member.user.email}
        </span>
      </div>

      {canManage && !isSelf ? (
        <Select
          value={member.role}
          onValueChange={(value) => handleRoleChange(value as MemberRole)}
          disabled={isPending}
        >
          <SelectTrigger size="sm" className="w-28 shrink-0" aria-label="Role">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="owner">Owner</SelectItem>
            <SelectItem value="member">Member</SelectItem>
          </SelectContent>
        </Select>
      ) : (
        <Badge variant="secondary" className="shrink-0 capitalize">
          {member.role}
        </Badge>
      )}

      {(canManage || isSelf) && (
        <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
          <AlertDialogTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="shrink-0 text-destructive hover:text-destructive"
              disabled={isPending}
            >
              {isSelf ? "Leave" : "Remove"}
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent size="sm">
            <AlertDialogHeader>
              <AlertDialogTitle>
                {isSelf ? "Leave this household?" : `Remove ${member.user.name}?`}
              </AlertDialogTitle>
              <AlertDialogDescription>
                {isSelf
                  ? "You'll lose access to this household's shared expenses and categories. Historical shared data is kept."
                  : `${member.user.name} will lose access to this household's shared expenses and categories.`}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={isPending}>Cancel</AlertDialogCancel>
              <AlertDialogAction
                variant="destructive"
                disabled={isPending}
                onClick={(event) => {
                  event.preventDefault()
                  handleConfirm()
                }}
              >
                {isSelf ? "Leave" : "Remove"}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
    </li>
  )
}

function MembersList({
  householdId,
  onLeft,
}: {
  householdId: string
  onLeft: () => void
}) {
  const { data, isLoading, isError } = useHouseholdMembers(householdId)
  const { data: session } = authClient.useSession()
  const { refetch: refetchHouseholds } = useHouseholds()
  const updateRole = useUpdateMemberRole(householdId)
  const removeMember = useRemoveMember(householdId)
  const leaveHousehold = useLeaveHousehold(householdId)
  const [error, setError] = useState<string | null>(null)

  const members = data?.members ?? []
  const currentUserId = session?.user.id
  const isOwner = useMyHouseholdRole(householdId) === "owner"

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading members…</p>
  }

  if (isError) {
    return (
      <p className="text-sm text-destructive" role="alert">
        Failed to load members.
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      <ul className="flex flex-col gap-2">
        {members.map((member) => (
          <MemberRow
            key={member.id}
            member={member}
            isSelf={member.userId === currentUserId}
            canManage={isOwner}
            onError={setError}
            onLeft={() => {
              refetchHouseholds()
              onLeft()
            }}
            updateRole={updateRole}
            removeMember={removeMember}
            leaveHousehold={leaveHousehold}
          />
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

export { MembersList }
