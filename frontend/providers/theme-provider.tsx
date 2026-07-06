"use client"

import * as React from "react"
import { ThemeProvider as NextThemesProvider, useTheme } from "next-themes"

import { useWorkspaceStore } from "@/stores/workspace-store"

const DEFAULT_THEME = "dark"
const WORKSPACE_THEMES_KEY = "workspace-themes"

function workspaceThemeKey(workspaceId: string | null) {
  return workspaceId ? `household:${workspaceId}` : "personal"
}

function readWorkspaceThemes(): Record<string, string> {
  try {
    const raw = localStorage.getItem(WORKSPACE_THEMES_KEY)
    return raw ? (JSON.parse(raw) as Record<string, string>) : {}
  } catch {
    return {}
  }
}

function readStoredTheme(workspaceKey: string) {
  return readWorkspaceThemes()[workspaceKey] ?? null
}

function writeStoredTheme(workspaceKey: string, theme: string) {
  try {
    const themes = readWorkspaceThemes()
    themes[workspaceKey] = theme
    localStorage.setItem(WORKSPACE_THEMES_KEY, JSON.stringify(themes))
  } catch {
    // Best-effort persistence -- the theme still applies for this session.
  }
}

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
      <ThemeHotkey />
      {children}
    </NextThemesProvider>
  )
}

// Applies the active workspace's saved theme (personal vs. this household) on
// every switch, so the applied theme follows the workspace per PRD §8. This
// covers the existing dark/light toggle only -- BUD-55 (M8) owns the actual
// multi-theme picker and moving this storage server-side so a household's
// theme is shared by every member, not just this browser.
function WorkspaceThemeSync() {
  const activeWorkspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  const { setTheme } = useTheme()

  React.useEffect(() => {
    setTheme(readStoredTheme(workspaceThemeKey(activeWorkspaceId)) ?? DEFAULT_THEME)
  }, [activeWorkspaceId, setTheme])

  return null
}

function isTypingTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) {
    return false
  }

  return (
    target.isContentEditable ||
    target.tagName === "INPUT" ||
    target.tagName === "TEXTAREA" ||
    target.tagName === "SELECT"
  )
}

function ThemeHotkey() {
  const { resolvedTheme, setTheme } = useTheme()
  const activeWorkspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)

  React.useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.defaultPrevented || event.repeat) {
        return
      }

      if (event.metaKey || event.ctrlKey || event.altKey) {
        return
      }

      if (event.key.toLowerCase() !== "d") {
        return
      }

      if (isTypingTarget(event.target)) {
        return
      }

      const next = resolvedTheme === "light" ? "dark" : "light"
      setTheme(next)
      writeStoredTheme(workspaceThemeKey(activeWorkspaceId), next)
    }

    window.addEventListener("keydown", onKeyDown)

    return () => {
      window.removeEventListener("keydown", onKeyDown)
    }
  }, [resolvedTheme, setTheme, activeWorkspaceId])

  return null
}

export { ThemeProvider }
