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
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ReceiptAttachments } from "@/features/attachments"
import { CategoryColor, useCategories, type Category } from "@/features/categories"
import { CurrencySelect } from "@/features/currency"
import { useCreateRecurringExpense } from "@/features/recurring"
import { ApiError } from "@/lib/api-client"

import { useCreateExpense, useCreateInstallmentExpense, useUpdateExpense } from "../api/mutations"
import {
  createExpenseSchema,
  expenseSchema,
  toExpensePayload,
  type CreateExpenseFormValues,
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
  expense: Expense,
  categories: Category[],
): DefaultValues<ExpenseFormValues> {
  return {
    description: expense.description,
    amount: Number(expense.amount),
    currency: expense.currency,
    spent_on: expense.spent_on,
    expense_group: getDefaultGroup(expense, categories),
    category_id: expense.category_id,
  }
}

function getCreateDefaultValues(): DefaultValues<CreateExpenseFormValues> {
  return {
    expense_type: "one_time",
    description: "",
    amount: undefined,
    currency: "PHP",
    expense_group: "other",
    category_id: "",
    spent_on: todayLocalDate(),
    installment_total: 2,
    start_on: todayLocalDate(),
    end_on: "",
  }
}

interface EditExpenseFieldsProps {
  expense: Expense
  categories: Category[]
  categoriesError: boolean
  onSuccess: () => void
}

function EditExpenseFields({
  expense,
  categories,
  categoriesError,
  onSuccess,
}: EditExpenseFieldsProps) {
  const update = useUpdateExpense()
  const isPending = update.isPending
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
      await update.mutateAsync({ id: expense.id, data: payload })
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
              <CurrencySelect value={field.value} onValueChange={field.onChange} />
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
                <Input type="date" {...field} disabled={!!expense.recurring_expense_id} />
              </FormControl>
              {expense.recurring_expense_id && (
                <p className="text-xs text-muted-foreground">
                  This date is set by the recurring rule and can&apos;t be changed here.
                </p>
              )}
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="expense_group"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Group</FormLabel>
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

      <ReceiptAttachments expenseId={expense.id} />

      <DialogFooter showCloseButton>
        <Button type="submit" form="expense-form" disabled={isPending}>
          {isPending ? (
            <span className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
          ) : (
            "Save expense"
          )}
        </Button>
      </DialogFooter>
    </Form>
  )
}

interface CreateExpenseFieldsProps {
  categories: Category[]
  categoriesError: boolean
  onSuccess: () => void
}

function CreateExpenseFields({
  categories,
  categoriesError,
  onSuccess,
}: CreateExpenseFieldsProps) {
  const createOneTime = useCreateExpense()
  const createInstallment = useCreateInstallmentExpense()
  const createRecurring = useCreateRecurringExpense()
  const isPending =
    createOneTime.isPending || createInstallment.isPending || createRecurring.isPending
  const [apiError, setApiError] = useState<string | null>(null)

  const form = useForm<CreateExpenseFormValues>({
    resolver: zodResolver(createExpenseSchema),
    defaultValues: getCreateDefaultValues(),
  })

  const expenseType = useWatch({ control: form.control, name: "expense_type" })
  const selectedGroup = useWatch({ control: form.control, name: "expense_group" })
  const categoryOptions = categories.filter(
    (category) => category.expense_group === selectedGroup,
  )

  async function onSubmit(values: CreateExpenseFormValues) {
    if (isPending) {
      return
    }

    setApiError(null)

    try {
      if (values.expense_type === "one_time") {
        await createOneTime.mutateAsync(
          toExpensePayload({
            description: values.description,
            amount: values.amount,
            currency: values.currency,
            spent_on: values.spent_on!,
            expense_group: values.expense_group,
            category_id: values.category_id,
          }),
        )
      } else if (values.expense_type === "installment") {
        await createInstallment.mutateAsync({
          description: values.description,
          amount: values.amount,
          currency: values.currency,
          spent_on: values.spent_on!,
          category_id: values.category_id,
          installment_total: values.installment_total!,
        })
      } else {
        await createRecurring.mutateAsync({
          category_id: values.category_id,
          description: values.description,
          amount: values.amount,
          currency: values.currency,
          start_on: values.start_on!,
          end_on: values.end_on ? values.end_on : null,
        })
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
          name="expense_type"
          render={({ field }) => (
            <FormItem className="sm:col-span-2">
              <FormLabel>Expense type</FormLabel>
              <FormControl>
                <RadioGroup
                  className="grid-cols-3"
                  value={field.value}
                  onValueChange={field.onChange}
                >
                  <label className="flex items-center gap-2 rounded-2xl border px-3 py-2 text-sm has-data-checked:border-primary">
                    <RadioGroupItem value="one_time" />
                    One-time
                  </label>
                  <label className="flex items-center gap-2 rounded-2xl border px-3 py-2 text-sm has-data-checked:border-primary">
                    <RadioGroupItem value="installment" />
                    Installment
                  </label>
                  <label className="flex items-center gap-2 rounded-2xl border px-3 py-2 text-sm has-data-checked:border-primary">
                    <RadioGroupItem value="recurring" />
                    Recurring
                  </label>
                </RadioGroup>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

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
              <CurrencySelect value={field.value} onValueChange={field.onChange} />
              <FormMessage />
            </FormItem>
          )}
        />

        {expenseType !== "recurring" && (
          <FormField
            control={form.control}
            name="spent_on"
            render={({ field }) => (
              <FormItem>
                <FormLabel>
                  {expenseType === "installment" ? "First installment date" : "Date"}
                </FormLabel>
                <FormControl>
                  <Input type="date" {...field} value={field.value ?? ""} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        )}

        {expenseType === "installment" && (
          <FormField
            control={form.control}
            name="installment_total"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Number of installments</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    inputMode="numeric"
                    min={2}
                    max={60}
                    step={1}
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
        )}

        {expenseType === "recurring" && (
          <>
            <FormField
              control={form.control}
              name="start_on"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Start date</FormLabel>
                  <FormControl>
                    <Input type="date" {...field} value={field.value ?? ""} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="end_on"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>End date (optional)</FormLabel>
                  <FormControl>
                    <Input type="date" {...field} value={field.value ?? ""} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </>
        )}

        <FormField
          control={form.control}
          name="expense_group"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Group</FormLabel>
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

  return expense ? (
    <EditExpenseFields
      expense={expense}
      categories={categories ?? []}
      categoriesError={categoriesError}
      onSuccess={onSuccess}
    />
  ) : (
    <CreateExpenseFields
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
