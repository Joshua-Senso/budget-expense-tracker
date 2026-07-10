"use client"

import * as React from "react"
import { ThemeProvider as NextThemesProvider, useTheme } from "next-themes"

import { useWorkspaceTheme } from "@/features/theme"

const DEFAULT_THEME = "dark"

function ThemeProvider({
  children,
  ...props
}: React.ComponentProps<typeof NextThemesProvider>) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme={DEFAULT_THEME}
      enableSystem={false}
      disableTransitionOnChange
      {...props}
    >
      <WorkspaceThemeSync />
      {children}
    </NextThemesProvider>
  )
}

// Applies the active workspace's stored theme (personal user profile, or this
// household's organization record) on every switch, per PRD §8/§11.
function WorkspaceThemeSync() {
  const { setTheme } = useTheme()
  const { theme, isPending } = useWorkspaceTheme()

  React.useEffect(() => {
    // Keep whatever's currently applied while the workspace's real theme is
    // still loading, instead of forcing DEFAULT_THEME and flashing.
    if (isPending) return
    setTheme(theme)
  }, [theme, isPending, setTheme])

  return null
}

export { ThemeProvider }
