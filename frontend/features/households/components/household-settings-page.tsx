"use client"

import { useState } from "react"
import { PlusIcon, UserPlusIcon } from "lucide-react"

import { Button } from "@/components/ui/button"

import { useHouseholds, useMyHouseholdRole } from "../api/queries"
import type { Household } from "../schemas"
import { CreateHouseholdDialog } from "./create-household-dialog"
import { InviteMemberDialog } from "./invite-member-dialog"
import { InvitationsList } from "./invitations-list"
import { MembersList } from "./members-list"
import { ReceivedInvitations } from "./received-invitations"

function HouseholdDetail({
  household,
  onLeft,
}: {
  household: Household
  onLeft: () => void
}) {
  const isOwner = useMyHouseholdRole(household.id) === "owner"
  const [inviteOpen, setInviteOpen] = useState(false)

  return (
    <div className="flex flex-col gap-6 rounded-3xl border bg-card p-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">{household.name}</h2>
          <p className="text-sm text-muted-foreground">/{household.slug}</p>
        </div>
        {isOwner && (
          <Button size="sm" className="gap-1.5" onClick={() => setInviteOpen(true)}>
            <UserPlusIcon />
            Invite member
          </Button>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <h3 className="text-sm font-medium text-muted-foreground">Members</h3>
        <MembersList householdId={household.id} onLeft={onLeft} />
      </div>

      {isOwner && (
        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-medium text-muted-foreground">
            Pending invitations
          </h3>
          <InvitationsList householdId={household.id} />
        </div>
      )}

      <InviteMemberDialog
        householdId={household.id}
        open={inviteOpen}
        onOpenChange={setInviteOpen}
      />
    </div>
  )
}

function HouseholdSettingsPage() {
  const { households, isPending } = useHouseholds()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [createOpen, setCreateOpen] = useState(false)

  const selected = households?.find((household) => household.id === selectedId)

  return (
    <section className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Households</h1>
        <p className="text-sm text-muted-foreground">
          Create shared households, invite members, and manage roles.
        </p>
      </div>

      <ReceivedInvitations />

      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-muted-foreground">Your households</h2>
        <Button size="sm" className="gap-1.5" onClick={() => setCreateOpen(true)}>
          <PlusIcon />
          Create household
        </Button>
      </div>

      {isPending && <p className="text-sm text-muted-foreground">Loading…</p>}

      {households && households.length === 0 && (
        <p className="text-sm text-muted-foreground">
          You don&apos;t belong to any household yet.
        </p>
      )}

      {households && households.length > 0 && (
        <ul className="flex flex-col gap-2">
          {households.map((household) => (
            <li key={household.id}>
              <button
                type="button"
                onClick={() =>
                  setSelectedId((current) =>
                    current === household.id ? null : household.id,
                  )
                }
                className="flex w-full items-center justify-between rounded-2xl border bg-card px-4 py-3 text-left transition-colors hover:bg-muted"
                aria-expanded={selectedId === household.id}
              >
                <span className="text-sm font-medium">{household.name}</span>
                <span className="text-xs text-muted-foreground">
                  {selectedId === household.id ? "Hide" : "Manage"}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {selected && (
        <HouseholdDetail household={selected} onLeft={() => setSelectedId(null)} />
      )}

      <CreateHouseholdDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        onCreated={(householdId) => setSelectedId(householdId)}
      />
    </section>
  )
}

export { HouseholdSettingsPage }
