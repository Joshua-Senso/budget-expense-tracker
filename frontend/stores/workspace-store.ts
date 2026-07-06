import { create } from "zustand"
import { createJSONStorage, persist } from "zustand/middleware"

type WorkspaceScope = "personal" | "household"

type WorkspaceState = {
  activeWorkspaceId: string | null
  activeWorkspaceScope: WorkspaceScope
  setActiveWorkspace: (workspace: {
    id: string | null
    scope?: WorkspaceScope
  }) => void
}

const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set) => ({
      activeWorkspaceId: null,
      activeWorkspaceScope: "personal",
      setActiveWorkspace: ({ id, scope = id ? "household" : "personal" }) => {
        set({ activeWorkspaceId: id, activeWorkspaceScope: scope })
      },
    }),
    {
      name: "active-workspace",
      storage: createJSONStorage(() => localStorage),
    },
  ),
)

export { useWorkspaceStore }
export type { WorkspaceScope, WorkspaceState }
