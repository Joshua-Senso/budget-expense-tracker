"use client"

import * as React from "react"

import { QueryProvider } from "@/providers/query-provider"
import { ThemeProvider } from "@/providers/theme-provider"
import { WorkspaceProvider } from "@/providers/workspace-provider"

function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <QueryProvider>
        <WorkspaceProvider>{children}</WorkspaceProvider>
      </QueryProvider>
    </ThemeProvider>
  )
}

export { Providers }
