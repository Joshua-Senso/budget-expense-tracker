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

import { householdSchema, type HouseholdFormValues } from "../schemas"
import { useCreateHousehold } from "../api/mutations"
import { useHouseholds } from "../api/queries"

function slugify(name: string) {
  return name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
}

interface CreateHouseholdDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreated: (householdId: string) => void
}

function CreateHouseholdForm({
  onSuccess,
}: {
  onSuccess: (householdId: string) => void
}) {
  const create = useCreateHousehold()
  const { refetch: refetchHouseholds } = useHouseholds()
  const [apiError, setApiError] = useState<string | null>(null)
  const [slugTouched, setSlugTouched] = useState(false)

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<HouseholdFormValues>({
    resolver: zodResolver(householdSchema),
    defaultValues: { name: "", slug: "" },
  })

  const nameField = register("name")

  async function onSubmit(data: HouseholdFormValues) {
    setApiError(null)
    try {
      const household = await create.mutateAsync(data)
      // Better Auth's own $listOrg atom listener refreshes `useListOrganizations()`
      // in the background on a short delay, which races the immediate selection
      // below. Refetch explicitly so the new household is guaranteed to be in
      // `households` before we select it.
      await refetchHouseholds()
      onSuccess((household as { id: string }).id)
    } catch {
      setApiError(
        "Could not create household. The slug may already be taken — try adjusting it.",
      )
    }
  }

  return (
    <>
      <form
        id="household-form"
        onSubmit={handleSubmit(onSubmit)}
        className="flex flex-col gap-4"
      >
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="household-name">Name</Label>
          <Input
            id="household-name"
            placeholder="e.g. The Santos Family"
            aria-invalid={!!errors.name}
            {...nameField}
            onChange={(event) => {
              nameField.onChange(event)
              if (!slugTouched) {
                setValue("slug", slugify(event.target.value), {
                  shouldValidate: true,
                })
              }
            }}
          />
          {errors.name && (
            <p className="text-xs text-destructive">{errors.name.message}</p>
          )}
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="household-slug">Slug</Label>
          <Input
            id="household-slug"
            placeholder="e.g. santos-family"
            aria-invalid={!!errors.slug}
            {...register("slug", {
              onChange: () => setSlugTouched(true),
            })}
          />
          {errors.slug && (
            <p className="text-xs text-destructive">{errors.slug.message}</p>
          )}
        </div>

        {apiError && (
          <p className="text-sm text-destructive" role="alert">
            {apiError}
          </p>
        )}
      </form>

      <DialogFooter showCloseButton>
        <Button type="submit" form="household-form" disabled={create.isPending}>
          {create.isPending ? (
            <span className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
          ) : (
            "Create"
          )}
        </Button>
      </DialogFooter>
    </>
  )
}

function CreateHouseholdDialog({
  open,
  onOpenChange,
  onCreated,
}: CreateHouseholdDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create household</DialogTitle>
        </DialogHeader>
        {open && (
          <CreateHouseholdForm
            onSuccess={(householdId) => {
              onOpenChange(false)
              onCreated(householdId)
            }}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}

export { CreateHouseholdDialog }
