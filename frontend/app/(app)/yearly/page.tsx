import { YearNav, YearlyOverview } from "@/features/dashboard"

function YearlyPage() {
  return (
    <section className="flex flex-col gap-6">
      <div>
        <p className="text-sm font-medium text-muted-foreground uppercase">
          Yearly overview
        </p>
        <YearNav />
      </div>

      <YearlyOverview />
    </section>
  )
}

export default YearlyPage
