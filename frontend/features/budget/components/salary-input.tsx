"use client"

import { useState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"

import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { toMonthKey, useMonthStore } from "@/stores/month-store"
import type { SelectedMonth } from "@/stores/month-store"

import { useUpsertMonthlySetting } from "../api/mutations"
import { useMonthlySetting } from "../api/queries"
import {
  monthlySettingSchema,
  type MonthlySetting,
  type MonthlySettingFormValues,
} from "../schemas"

interface SalaryFormProps {
  month: SelectedMonth
  setting: MonthlySetting | null | undefined
}

function SalaryForm({ month, setting }: SalaryFormProps) {
  const [saved, setSaved] = useState(false)
  const upsert = useUpsertMonthlySetting(month)

  const form = useForm<MonthlySettingFormValues>({
    resolver: zodResolver(monthlySettingSchema),
    defaultValues: {
      monthly_net_salary: setting
        ? Number(setting.monthly_net_salary)
        : undefined,
    },
  })

  async function onSubmit(values: MonthlySettingFormValues) {
    setSaved(false)
    try {
      await upsert.mutateAsync(values)
      setSaved(true)
    } catch {
      // surfaced via upsert.isError below
    }
  }

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="flex flex-col gap-2 sm:flex-row sm:items-start sm:gap-3"
      >
        <FormField
          control={form.control}
          name="monthly_net_salary"
          render={({ field }) => (
            <FormItem className="flex-1">
              <FormLabel>Monthly net salary</FormLabel>
              <FormControl>
                <Input
                  type="number"
                  inputMode="decimal"
                  min="0"
                  step="0.01"
                  placeholder="0.00"
                  {...field}
                  value={field.value ?? ""}
                  onChange={(event) => {
                    setSaved(false)
                    const value = event.target.valueAsNumber
                    field.onChange(Number.isNaN(value) ? undefined : value)
                  }}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit" disabled={upsert.isPending} className="sm:mt-6.5">
          {upsert.isPending ? (
            <span className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
          ) : (
            "Save"
          )}
        </Button>

        {upsert.isError && (
          <p className="text-sm text-destructive sm:self-center" role="alert">
            Could not save salary. Please try again.
          </p>
        )}
        {saved && !upsert.isError && (
          <p className="text-sm text-muted-foreground sm:self-center">Saved.</p>
        )}
      </form>
    </Form>
  )
}

function SalaryInput() {
  const year = useMonthStore((state) => state.year)
  const monthNumber = useMonthStore((state) => state.month)
  const month = { year, month: monthNumber }
  const { data: setting, isLoading, isError } = useMonthlySetting(month)

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading salary…</p>
  }

  return (
    <div className="flex flex-col gap-2">
      <SalaryForm
        key={`${toMonthKey(month)}-${setting?.updated_at ?? "empty"}`}
        month={month}
        setting={setting}
      />
      {isError && (
        <p className="text-sm text-destructive" role="alert">
          Failed to load the salary for this month.
        </p>
      )}
    </div>
  )
}

export { SalaryInput }
