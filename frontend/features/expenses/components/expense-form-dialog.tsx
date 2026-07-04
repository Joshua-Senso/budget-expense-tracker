"use client"

import { useState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm, useWatch } from "react-hook-form"
import type { DefaultValues } from "react-hook-form"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { CategoryColor, useCategories, type Category } from "@/features/categories"
import { ApiError } from "@/lib/api-client"

import { useCreateExpense, useUpdateExpense } from "../api/mutations"
import {
  expenseSchema,
  toExpensePayload,
  type Expense,
  type ExpenseFormValues,
} from "../schemas"

function todayLocalDate() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, "0")
  const day = String(now.getDate()).padStart(2, "0")

  return `${year}-${month}-${day}`
}

function getErrorDetail(err: ApiError) {
  return typeof err.body === "object" && err.body !== null && "detail" in err.body
    ? String((err.body as { detail?: unknown }).detail)
    : null
}

function getSubmitErrorMessage(err: unknown) {
  if (err instanceof ApiError && err.status === 404) {
    const detail = getErrorDetail(err)

    if (detail === "Category not found.") {
      return "Choose one of your categories before saving."
    }
    if (detail === "Expense not found.") {
      return "This expense no longer exists. Refresh the page and try again."
    }
  }

  return "Could not save expense. Please try again."
}

function getDefaultGroup(expense?: Expense, categories?: Category[]) {
  const category = categories?.find((c) => c.id === expense?.category_id)
  return category?.expense_group ?? "other"
}

function getDefaultValues(
  expense: Expense | undefined,
  categories: Category[],
): DefaultValues<ExpenseFormValues> {
  return {
    description: expense?.description ?? "",
    amount: expense ? Number(expense.amount) : undefined,
    currency: expense?.currency ?? "PHP",
    spent_on: expense?.spent_on ?? todayLocalDate(),
    expense_group: getDefaultGroup(expense, categories),
    category_id: expense?.category_id ?? "",
  }
}

interface ExpenseFormFieldsProps {
  expense?: Expense
  categories: Category[]
  categoriesError: boolean
  onSuccess: () => void
}

function ExpenseFormFields({
  expense,
  categories,
  categoriesError,
  onSuccess,
}: ExpenseFormFieldsProps) {
  const isEdit = !!expense
  const create = useCreateExpense()
  const update = useUpdateExpense()
  const isPending = create.isPending || update.isPending
  const [apiError, setApiError] = useState<string | null>(null)

  const form = useForm<ExpenseFormValues>({
    resolver: zodResolver(expenseSchema),
    defaultValues: getDefaultValues(expense, categories),
  })

  const selectedGroup = useWatch({
    control: form.control,
    name: "expense_group",
  })
  const categoryOptions = categories.filter(
    (category) => category.expense_group === selectedGroup,
  )

  async function onSubmit(values: ExpenseFormValues) {
    if (isPending) {
      return
    }

    setApiError(null)
    const payload = toExpensePayload(values)

    try {
      if (isEdit && expense) {
        await update.mutateAsync({ id: expense.id, data: payload })
      } else {
        await create.mutateAsync(payload)
      }
      onSuccess()
    } catch (err) {
      setApiError(getSubmitErrorMessage(err))
    }
  }

  return (
    <Form {...form}>
      <form
        id="expense-form"
        onSubmit={form.handleSubmit(onSubmit)}
        className="grid gap-4 sm:grid-cols-2"
      >
        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem className="sm:col-span-2">
              <FormLabel>Description</FormLabel>
              <FormControl>
                <Input placeholder="e.g. Lunch at work" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="amount"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Amount</FormLabel>
              <FormControl>
                <Input
                  type="number"
                  inputMode="decimal"
                  min="0.01"
                  step="0.01"
                  placeholder="0.00"
                  {...field}
                  value={field.value ?? ""}
                  onChange={(event) => {
                    const value = event.target.valueAsNumber
                    field.onChange(Number.isNaN(value) ? undefined : value)
                  }}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="currency"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Currency</FormLabel>
              <FormControl>
                <Input
                  maxLength={3}
                  className="uppercase"
                  placeholder="PHP"
                  {...field}
                  onChange={(event) => field.onChange(event.target.value.toUpperCase())}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="spent_on"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Date</FormLabel>
              <FormControl>
                <Input type="date" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="expense_group"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Expense type</FormLabel>
              <Select
                value={field.value}
                onValueChange={(value) => {
                  field.onChange(value)
                  form.setValue("category_id", "", {
                    shouldValidate: form.formState.isSubmitted,
                  })
                }}
              >
                <FormControl>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="card">Card</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="category_id"
          render={({ field }) => (
            <FormItem className="sm:col-span-2">
              <FormLabel>Category</FormLabel>
              <Select
                value={field.value}
                disabled={categoriesError || categoryOptions.length === 0}
                onValueChange={field.onChange}
              >
                <FormControl>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {categoryOptions.map((category) => (
                    <SelectItem key={category.id} value={category.id}>
                      <CategoryColor color={category.color} className="size-3" />
                      {category.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {categoriesError && (
                <p className="text-xs text-destructive" role="alert">
                  Failed to load categories. Refresh the page and try again.
                </p>
              )}
              {!categoriesError && categoryOptions.length === 0 && (
                <p className="text-xs text-muted-foreground">
                  Add a {selectedGroup} category before saving this expense.
                </p>
              )}
              <FormMessage />
            </FormItem>
          )}
        />

        {apiError && (
          <p className="text-sm text-destructive sm:col-span-2" role="alert">
            {apiError}
          </p>
        )}
      </form>

      <DialogFooter showCloseButton>
        <Button type="submit" form="expense-form" disabled={isPending}>
          {isPending ? (
            <span className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
          ) : isEdit ? (
            "Save expense"
          ) : (
            "Add expense"
          )}
        </Button>
      </DialogFooter>
    </Form>
  )
}

interface ExpenseFormContentProps {
  expense?: Expense
  onSuccess: () => void
}

function ExpenseFormContent({ expense, onSuccess }: ExpenseFormContentProps) {
  const { data: categories, isLoading, isError: categoriesError } = useCategories()

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading…</p>
  }

  return (
    <ExpenseFormFields
      expense={expense}
      categories={categories ?? []}
      categoriesError={categoriesError}
      onSuccess={onSuccess}
    />
  )
}

interface ExpenseFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  expense?: Expense
}

function ExpenseFormDialog({ open, onOpenChange, expense }: ExpenseFormDialogProps) {
  const isEdit = !!expense

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit expense" : "Add expense"}</DialogTitle>
        </DialogHeader>
        {open && (
          <ExpenseFormContent
            key={expense?.id ?? "new"}
            expense={expense}
            onSuccess={() => onOpenChange(false)}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}

export { ExpenseFormDialog }
