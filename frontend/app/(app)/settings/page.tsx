import { HouseholdSettingsPage } from "@/features/households"
import { ThemePicker } from "@/features/theme"

export default function Page() {
  return (
    <div className="flex flex-col gap-8">
      <HouseholdSettingsPage />

      <section className="flex flex-col gap-4">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Appearance</h2>
          <p className="text-sm text-muted-foreground">
            Choose a theme for the active workspace.
          </p>
        </div>
        <ThemePicker />
      </section>
    </div>
  )
}
