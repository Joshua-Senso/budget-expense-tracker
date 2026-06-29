"use client"

import * as React from "react"

type WorkspaceScope = "personal" | "household"

type WorkspaceState = {
  activeWorkspaceId: string | null
  activeWorkspaceScope: WorkspaceScope
  setActiveWorkspace: (workspace: {
    id: string | null
    scope?: WorkspaceScope
  }) => void
}

const WorkspaceContext = React.createContext<WorkspaceState | null>(null)

function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const [activeWorkspaceId, setActiveWorkspaceId] = React.useState<string | null>(
    null,
  )
  const [activeWorkspaceScope, setActiveWorkspaceScope] =
    React.useState<WorkspaceScope>("personal")

  function setActiveWorkspace({
    id,
    scope = id ? "household" : "personal",
  }: {
    id: string | null
    scope?: WorkspaceScope
  }) {
    setActiveWorkspaceId(id)
    setActiveWorkspaceScope(scope)
  }

  return (
    <WorkspaceContext.Provider
      value={{ activeWorkspaceId, activeWorkspaceScope, setActiveWorkspace }}
    >
      {children}
    </WorkspaceContext.Provider>
  )
}

function useWorkspace() {
  const context = React.useContext(WorkspaceContext)
  if (context === null) {
    throw new Error("useWorkspace must be used within WorkspaceProvider")
  }
  return context
}

export { WorkspaceProvider, useWorkspace }
export type { WorkspaceScope, WorkspaceState }
