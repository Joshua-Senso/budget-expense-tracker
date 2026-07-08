"use client"

import { useState } from "react"
import { useTheme } from "next-themes"

import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import { useSetWorkspaceTheme } from "../api/mutations"
import { useWorkspaceTheme } from "../api/queries"
import { THEME_LABELS, THEME_VALUES } from "../constants"
import type { Theme } from "../schemas"

function ThemePicker() {
  const { setTheme } = useTheme()
  const { theme, isPending, scope, household } = useWorkspaceTheme()
  const { mutate, isPending: isSaving } = useSetWorkspaceTheme()
  const [error, setError] = useState<string | null>(null)

  function handleChange(next: Theme) {
    const previous = theme
    setError(null)
    // Apply immediately (PRD §11), independent of the save round trip.
    setTheme(next)
    mutate(next, {
      onError: (mutationError) => {
        setTheme(previous)
        setError(
          mutationError instanceof Error
            ? mutationError.message
            : "Couldn't update the theme. Please try again.",
        )
      },
    })
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <Select
          value={theme}
          onValueChange={(value) => handleChange(value as Theme)}
          disabled={isPending || isSaving}
        >
          <SelectTrigger className="w-[180px]" aria-label="Theme">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {THEME_VALUES.map((value) => (
              <SelectItem key={value} value={value}>
                {THEME_LABELS[value]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {scope === "household" && (
          <Badge variant="secondary" className="shrink-0">
            Shared
          </Badge>
        )}
      </div>
      <p className="text-xs text-muted-foreground">
        {scope === "household" && household
          ? `Applies to everyone in ${household.name}.`
          : "Applies only to your personal workspace."}
      </p>
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  )
}

export { ThemePicker }
