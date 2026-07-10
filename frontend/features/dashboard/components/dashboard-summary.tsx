"use client"

import { CategoryColor } from "@/features/categories"
import { SalaryInput } from "@/features/budget"
import { useIsHouseholdWorkspace } from "@/hooks/use-is-household-workspace"
import { formatCurrency } from "@/lib/format"
import { cn } from "@/lib/utils"
import { useMonthStore } from "@/stores/month-store"

import { useDashboardSummary } from "../api/queries"
import type {
  CategoryBreakdown,
  DashboardSummaryData,
  ExpenseGroupBreakdown,
} from "../schemas"

const HIGH_USAGE_THRESHOLD = 80
const OVER_BUDGET_THRESHOLD = 100

type UsageTone = "neutral" | "high" | "over"

function getUsageTone(percentUsed: number | null): UsageTone {
  if (percentUsed === null) {
    return "neutral"
  }
  if (percentUsed >= OVER_BUDGET_THRESHOLD) {
    return "over"
  }
  if (percentUsed >= HIGH_USAGE_THRESHOLD) {
    return "high"
  }
  return "neutral"
}

function CategoryRow({
  category,
  baseCurrency,
}: {
  category: CategoryBreakdown
  baseCurrency: string
}) {
  return (
    <li className="flex items-center gap-2 text-sm">
      <CategoryColor color={category.color} className="size-3" />
      <span className="flex-1 truncate text-muted-foreground">
        {category.name}
      </span>
      <span className="font-medium">
        {formatCurrency(category.total, baseCurrency)}
      </span>
    </li>
  )
}

interface GroupCardProps {
  title: string
  group: ExpenseGroupBreakdown
  baseCurrency: string
}

function GroupCard({ title, group, baseCurrency }: GroupCardProps) {
  return (
    <div className="flex flex-col gap-3 rounded-3xl border bg-card p-5 shadow-sm">
      <div className="flex items-baseline justify-between">
        <h3 className="text-sm font-medium text-muted-foreground uppercase">
          {title}
        </h3>
        <span className="text-xl font-semibold">
          {formatCurrency(group.total, baseCurrency)}
        </span>
      </div>

      {group.categories.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No {title.toLowerCase()} expenses yet.
        </p>
      ) : (
        <ul className="flex flex-col gap-1.5">
          {group.categories.map((category) => (
            <CategoryRow
              key={category.category_id}
              category={category}
              baseCurrency={baseCurrency}
            />
          ))}
        </ul>
      )}
    </div>
  )
}

function BudgetSummary({ summary }: { summary: DashboardSummaryData }) {
  const isHouseholdWorkspace = useIsHouseholdWorkspace()
  const percentUsed =
    summary.percent_used === null ? null : Number(summary.percent_used)
  const tone = getUsageTone(percentUsed)

  return (
    <div className="flex flex-col gap-4 rounded-3xl border bg-card p-5 shadow-sm">
      <div className="flex flex-col gap-1">
        <p className="text-sm font-medium text-muted-foreground uppercase">
          Budget
        </p>
        {/* Salary is a personal month setting (no household_id support yet) --
            shown here, saving it would silently write to the user's personal
            setting with no effect on the household summary being viewed. */}
        {!isHouseholdWorkspace && <SalaryInput />}
      </div>

      {isHouseholdWorkspace ? (
        <p className="text-sm text-muted-foreground">
          Household budgets aren&apos;t supported yet — salary tracking is
          personal-workspace only.
        </p>
      ) : summary.monthly_net_salary === null ? (
        <p className="text-sm text-muted-foreground">
          Set a monthly salary to track remaining balance and usage.
        </p>
      ) : (
        <>
          <div className="flex items-baseline justify-between">
            <span className="text-sm text-muted-foreground">Remaining</span>
            <span
              className={cn(
                "text-xl font-semibold",
                tone === "over" && "text-destructive"
              )}
            >
              {formatCurrency(summary.remaining ?? "0", summary.base_currency)}
            </span>
          </div>

          <div className="flex flex-col gap-1.5">
            <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
              <div
                className={cn(
                  "h-full rounded-full transition-[width]",
                  tone === "over" && "bg-destructive",
                  tone === "high" && "bg-amber-500",
                  tone === "neutral" && "bg-primary"
                )}
                style={{ width: `${Math.min(percentUsed ?? 0, 100)}%` }}
              />
            </div>
            <p
              className={cn(
                "text-sm",
                tone === "over" && "text-destructive",
                tone === "high" && "text-amber-600 dark:text-amber-400",
                tone === "neutral" && "text-muted-foreground"
              )}
              role={tone !== "neutral" ? "alert" : undefined}
            >
              {percentUsed !== null ? percentUsed.toFixed(1) : 0}% of salary
              used
              {tone === "over" && " — over budget"}
              {tone === "high" && " — approaching your limit"}
            </p>
          </div>
        </>
      )}
    </div>
  )
}

function DashboardSummary() {
  const year = useMonthStore((state) => state.year)
  const month = useMonthStore((state) => state.month)
  const { data: summary, isLoading, isError } = useDashboardSummary({
    year,
    month,
  })

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading dashboard…</p>
  }

  if (isError || !summary) {
    return (
      <p className="text-sm text-destructive" role="alert">
        Failed to load the dashboard summary.
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <GroupCard
          title="Card"
          group={summary.card}
          baseCurrency={summary.base_currency}
        />
        <GroupCard
          title="Other"
          group={summary.other}
          baseCurrency={summary.base_currency}
        />
      </div>
      <BudgetSummary summary={summary} />
    </div>
  )
}

export { DashboardSummary }
