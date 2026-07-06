"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import { inviteMemberSchema, type InviteMemberFormValues } from "../schemas"
import { useInviteMember } from "../api/mutations"

interface InviteMemberDialogProps {
  householdId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

function InviteMemberForm({
  householdId,
  onSuccess,
}: {
  householdId: string
  onSuccess: () => void
}) {
  const invite = useInviteMember(householdId)
  const [apiError, setApiError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<InviteMemberFormValues>({
    resolver: zodResolver(inviteMemberSchema),
    defaultValues: { email: "", role: "member" },
  })

  async function onSubmit(data: InviteMemberFormValues) {
    setApiError(null)
    try {
      await invite.mutateAsync(data)
      onSuccess()
    } catch {
      setApiError(
        "Could not send invitation. The person may already be a member or invited.",
      )
    }
  }

  return (
    <>
      <form
        id="invite-member-form"
        onSubmit={handleSubmit(onSubmit)}
        className="flex flex-col gap-4"
      >
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="invite-email">Email</Label>
          <Input
            id="invite-email"
            type="email"
            placeholder="name@example.com"
            aria-invalid={!!errors.email}
            {...register("email")}
          />
          {errors.email && (
            <p className="text-xs text-destructive">{errors.email.message}</p>
          )}
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="invite-role">Role</Label>
          <Select
            defaultValue="member"
            onValueChange={(value) =>
              setValue("role", value as InviteMemberFormValues["role"], {
                shouldValidate: true,
              })
            }
          >
            <SelectTrigger id="invite-role" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="member">Member</SelectItem>
              <SelectItem value="owner">Owner</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {apiError && (
          <p className="text-sm text-destructive" role="alert">
            {apiError}
          </p>
        )}
      </form>

      <DialogFooter showCloseButton>
        <Button type="submit" form="invite-member-form" disabled={invite.isPending}>
          {invite.isPending ? (
            <span className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
          ) : (
            "Send invite"
          )}
        </Button>
      </DialogFooter>
    </>
  )
}

function InviteMemberDialog({
  householdId,
  open,
  onOpenChange,
}: InviteMemberDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Invite a member</DialogTitle>
        </DialogHeader>
        {open && (
          <InviteMemberForm
            householdId={householdId}
            onSuccess={() => onOpenChange(false)}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}

export { InviteMemberDialog }
