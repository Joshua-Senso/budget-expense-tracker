const features = [
  "Multi-currency expense tracking",
  "Monthly budget & salary insights",
  "Shared household budgets",
]

export default function Page() {
  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-8 bg-background px-6 py-16 text-center text-foreground">
      <div className="flex flex-col items-center gap-3">
        <span className="rounded-full border px-3 py-1 text-xs font-medium tracking-wide text-muted-foreground uppercase">
          Coming soon
        </span>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
          Expense Tracker
        </h1>
        <p className="max-w-md text-pretty text-muted-foreground">
          Private budgeting for you and your household — track spending, stay on
          budget, and see where your money goes.
        </p>
      </div>

      <ul className="flex flex-col gap-2 text-sm text-muted-foreground">
        {features.map((feature) => (
          <li key={feature} className="flex items-center justify-center gap-2">
            <span aria-hidden className="size-1.5 rounded-full bg-primary" />
            {feature}
          </li>
        ))}
      </ul>

      <footer className="text-xs text-muted-foreground">
        © {new Date().getFullYear()} Expense Tracker
      </footer>
    </main>
  )
}
