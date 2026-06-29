"use client"

import * as React from "react"

import { useWorkspaceStore } from "@/stores/workspace-store"

function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  return children
}

export { WorkspaceProvider, useWorkspaceStore as useWorkspace }
export type { WorkspaceScope, WorkspaceState } from "@/stores/workspace-store"
