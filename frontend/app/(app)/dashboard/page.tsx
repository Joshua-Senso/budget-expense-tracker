import { ExpenseQuickEntry } from "@/features/expenses"

function DashboardPage() {
  return (
    <section className="flex flex-col gap-6">
      <div>
        <p className="text-sm font-medium text-muted-foreground uppercase">
          Dashboard
        </p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight">
          This month
        </h1>
        <p className="mt-2 max-w-xl text-muted-foreground">
          Start by recording one-time expenses. Totals and monthly breakdowns land
          in the next milestone.
        </p>
      </div>

      <ExpenseQuickEntry />
    </section>
  )
}

export default DashboardPage
