import { create } from "zustand"

type WorkspaceScope = "personal" | "household"

type WorkspaceState = {
  activeWorkspaceId: string | null
  activeWorkspaceScope: WorkspaceScope
  setActiveWorkspace: (workspace: {
    id: string | null
    scope?: WorkspaceScope
  }) => void
}

const useWorkspaceStore = create<WorkspaceState>((set) => ({
  activeWorkspaceId: null,
  activeWorkspaceScope: "personal",
  setActiveWorkspace: ({ id, scope = id ? "household" : "personal" }) => {
    set({ activeWorkspaceId: id, activeWorkspaceScope: scope })
  },
}))

export { useWorkspaceStore }
export type { WorkspaceScope, WorkspaceState }
