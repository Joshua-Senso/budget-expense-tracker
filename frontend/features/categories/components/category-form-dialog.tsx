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

import { ApiError } from "@/lib/api-client"
import { categorySchema, type Category, type CategoryFormValues } from "../schemas"
import { useCreateCategory, useUpdateCategory } from "../api/mutations"

interface CategoryFormContentProps {
  category?: Category
  onSuccess: () => void
}

function CategoryFormContent({ category, onSuccess }: CategoryFormContentProps) {
  const isEdit = !!category
  const create = useCreateCategory()
  const update = useUpdateCategory()
  const isPending = create.isPending || update.isPending

  const defaultColor = category?.color ?? "#6366f1"
  const [colorPreview, setColorPreview] = useState(defaultColor)
  const [apiError, setApiError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<CategoryFormValues>({
    resolver: zodResolver(categorySchema),
    defaultValues: {
      name: category?.name ?? "",
      color: defaultColor,
      expense_group: category?.expense_group ?? "other",
    },
  })

  function handleColorChange(hex: string) {
    setColorPreview(hex)
    setValue("color", hex, { shouldValidate: true })
  }

  async function onSubmit(data: CategoryFormValues) {
    setApiError(null)
    try {
      if (isEdit && category) {
        await update.mutateAsync({ id: category.id, data })
      } else {
        await create.mutateAsync(data)
      }
      onSuccess()
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setApiError("A category with that name already exists.")
      } else {
        setApiError("Something went wrong. Please try again.")
      }
    }
  }

  return (
    <>
      <form
        id="category-form"
        onSubmit={handleSubmit(onSubmit)}
        className="flex flex-col gap-4"
      >
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="cat-name">Name</Label>
          <Input
            id="cat-name"
            placeholder="e.g. Groceries"
            aria-invalid={!!errors.name}
            {...register("name")}
          />
          {errors.name && (
            <p className="text-xs text-destructive">{errors.name.message}</p>
          )}
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="cat-color">Color</Label>
          <div className="flex items-center gap-2">
            <input
              id="cat-color"
              type="color"
              value={colorPreview}
              onChange={(e) => handleColorChange(e.target.value)}
              className="size-9 cursor-pointer rounded-full border border-transparent bg-transparent p-0.5 outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30"
            />
            <Input
              placeholder="#6366f1"
              value={colorPreview}
              onChange={(e) => handleColorChange(e.target.value)}
              aria-invalid={!!errors.color}
              className="font-mono uppercase"
              maxLength={7}
            />
          </div>
          {errors.color && (
            <p className="text-xs text-destructive">{errors.color.message}</p>
          )}
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="cat-group">Group</Label>
          <Select
            defaultValue={category?.expense_group ?? "other"}
            onValueChange={(v) =>
              setValue("expense_group", v as "card" | "other", {
                shouldValidate: true,
              })
            }
          >
            <SelectTrigger
              id="cat-group"
              className="w-full"
              aria-invalid={!!errors.expense_group}
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="card">Card</SelectItem>
              <SelectItem value="other">Other</SelectItem>
            </SelectContent>
          </Select>
          {errors.expense_group && (
            <p className="text-xs text-destructive">
              {errors.expense_group.message}
            </p>
          )}
        </div>

        {apiError && (
          <p className="text-sm text-destructive" role="alert">
            {apiError}
          </p>
        )}
      </form>

      <DialogFooter showCloseButton>
        <Button type="submit" form="category-form" disabled={isPending}>
          {isPending ? (
            <span className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
          ) : isEdit ? (
            "Save"
          ) : (
            "Add"
          )}
        </Button>
      </DialogFooter>
    </>
  )
}

interface CategoryFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  category?: Category
}

function CategoryFormDialog({
  open,
  onOpenChange,
  category,
}: CategoryFormDialogProps) {
  const isEdit = !!category
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit category" : "Add category"}</DialogTitle>
        </DialogHeader>
        {open && (
          <CategoryFormContent
            key={category?.id ?? "new"}
            category={category}
            onSuccess={() => onOpenChange(false)}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}

export { CategoryFormDialog }
