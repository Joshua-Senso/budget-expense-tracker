"use client"

import { useState } from "react"
import { PencilIcon, Trash2Icon, PlusIcon } from "lucide-react"

import { Button } from "@/components/ui/button"

import { ApiError } from "@/lib/api-client"
import { useCategories } from "../api/queries"
import { useDeleteCategory } from "../api/mutations"
import { CategoryColor } from "./category-color"
import { CategoryFormDialog } from "./category-form-dialog"
import type { Category } from "../schemas"

function CategoriesPage() {
  const { data: categories, isLoading, isError } = useCategories()
  const deleteCategory = useDeleteCategory()

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editTargetId, setEditTargetId] = useState<string | undefined>(undefined)
  const [deleteErrors, setDeleteErrors] = useState<Record<string, string>>({})
  const [pendingDeleteIds, setPendingDeleteIds] = useState<Set<string>>(
    new Set(),
  )

  const editTarget = categories?.find((c) => c.id === editTargetId)

  function openAdd() {
    setEditTargetId(undefined)
    setDialogOpen(true)
  }

  function openEdit(category: Category) {
    setEditTargetId(category.id)
    setDialogOpen(true)
  }

  async function handleDelete(category: Category) {
    setDeleteErrors((prev) => {
      const next = { ...prev }
      delete next[category.id]
      return next
    })
    setPendingDeleteIds((prev) => new Set(prev).add(category.id))
    try {
      await deleteCategory.mutateAsync(category.id)
    } catch (err) {
      let message = "Could not delete category."
      if (err instanceof ApiError && err.status === 409) {
        message = "You must keep at least one category."
      }
      setDeleteErrors((prev) => ({ ...prev, [category.id]: message }))
    } finally {
      setPendingDeleteIds((prev) => {
        const next = new Set(prev)
        next.delete(category.id)
        return next
      })
    }
  }

  return (
    <section className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Categories</h1>
          <p className="text-sm text-muted-foreground">
            Organise your expenses by category.
          </p>
        </div>
        <Button onClick={openAdd} size="sm" className="gap-1.5">
          <PlusIcon />
          Add category
        </Button>
      </div>

      {isLoading && (
        <p className="text-sm text-muted-foreground">Loading…</p>
      )}

      {isError && (
        <p className="text-sm text-destructive" role="alert">
          Failed to load categories.
        </p>
      )}

      {categories && categories.length === 0 && (
        <p className="text-sm text-muted-foreground">No categories yet.</p>
      )}

      {categories && categories.length > 0 && (
        <ul className="flex flex-col gap-2">
          {categories.map((category) => (
            <li key={category.id} className="flex flex-col gap-1">
              <div className="flex items-center gap-3 rounded-2xl border bg-card px-4 py-3">
                <CategoryColor color={category.color} className="size-5" />

                <div className="min-w-0 flex-1">
                  <span className="truncate text-sm font-medium">
                    {category.name}
                  </span>
                  <span className="ml-2 text-xs capitalize text-muted-foreground">
                    {category.expense_group}
                  </span>
                </div>

                <div className="flex shrink-0 items-center gap-1">
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    aria-label={`Edit ${category.name}`}
                    onClick={() => openEdit(category)}
                  >
                    <PencilIcon />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    aria-label={`Delete ${category.name}`}
                    onClick={() => handleDelete(category)}
                    disabled={pendingDeleteIds.has(category.id)}
                    className="text-destructive hover:text-destructive"
                  >
                    <Trash2Icon />
                  </Button>
                </div>
              </div>

              {deleteErrors[category.id] && (
                <p className="px-4 text-xs text-destructive" role="alert">
                  {deleteErrors[category.id]}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}

      <CategoryFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        category={editTarget}
      />
    </section>
  )
}

export { CategoriesPage }
