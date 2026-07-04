import { DashboardSummary, MonthNav } from "@/features/dashboard"
import { ExpenseList, ExpenseQuickEntry } from "@/features/expenses"

function DashboardPage() {
  return (
    <section className="flex flex-col gap-6">
      <div>
        <p className="text-sm font-medium text-muted-foreground uppercase">
          Dashboard
        </p>
        <MonthNav />
      </div>

      <DashboardSummary />

      <ExpenseQuickEntry />
      <ExpenseList />
    </section>
  )
}

export default DashboardPage
