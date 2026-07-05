import { YearNav, YearlyOverview } from "@/features/dashboard"
import { ImportExportControls } from "@/features/import-export"

function YearlyPage() {
  return (
    <section className="flex flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-muted-foreground uppercase">
            Yearly overview
          </p>
          <YearNav />
        </div>
        <ImportExportControls />
      </div>

      <YearlyOverview />
    </section>
  )
}

export default YearlyPage
