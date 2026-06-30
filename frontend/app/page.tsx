import Link from "next/link"

import { buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const features = [
  {
    title: "Multi-currency tracking",
    description:
      "Log expenses in any currency. Each entry is auto-converted to your base currency so totals always make sense.",
  },
  {
    title: "Budget & salary insights",
    description:
      "Set a monthly budget, record your income, and see exactly how much is left — and where it went.",
  },
  {
    title: "Shared household budgets",
    description:
      "Invite household members, pool expenses, and keep everyone on the same page without sharing credentials.",
  },
  {
    title: "Import & export",
    description:
      "Bulk-import transactions from a CSV or export your data at any time — no lock-in.",
  },
]

export default function Page() {
  return (
    <div className="flex min-h-svh flex-col bg-background text-foreground">
      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col items-center justify-center gap-16 px-6 py-24 text-center">
        <section className="flex flex-col items-center gap-6">
          <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
            Expense Tracker
          </h1>
          <p className="max-w-lg text-pretty text-lg text-muted-foreground">
            Private budgeting for you and your household — track spending across
            currencies, stay on budget, and see where your money goes.
          </p>
          <Link
            href="/sign-in"
            className={cn(buttonVariants({ size: "lg" }), "mt-2")}
          >
            Sign in to get started
          </Link>
        </section>

        <section aria-labelledby="features-heading" className="w-full">
          <h2
            id="features-heading"
            className="mb-8 text-xs font-medium uppercase tracking-widest text-muted-foreground"
          >
            What you get
          </h2>
          <ul className="grid gap-4 sm:grid-cols-2">
            {features.map(({ title, description }) => (
              <li
                key={title}
                className="rounded-2xl border bg-card p-6 text-left shadow-card"
              >
                <h3 className="font-semibold">{title}</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  {description}
                </p>
              </li>
            ))}
          </ul>
        </section>
      </main>

      <footer className="py-8 text-center text-xs text-muted-foreground">
        © {new Date().getFullYear()} Expense Tracker
      </footer>
    </div>
  )
}
