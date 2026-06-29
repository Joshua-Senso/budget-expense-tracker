import { beforeEach, expect, test } from "vitest"

import { useWorkspaceStore } from "@/stores/workspace-store"

beforeEach(() => {
  useWorkspaceStore.setState({
    activeWorkspaceId: null,
    activeWorkspaceScope: "personal",
  })
})

test("workspace store tracks personal and household scopes", () => {
  useWorkspaceStore.getState().setActiveWorkspace({ id: "household-1" })

  expect(useWorkspaceStore.getState()).toMatchObject({
    activeWorkspaceId: "household-1",
    activeWorkspaceScope: "household",
  })

  useWorkspaceStore.getState().setActiveWorkspace({ id: null })

  expect(useWorkspaceStore.getState()).toMatchObject({
    activeWorkspaceId: null,
    activeWorkspaceScope: "personal",
  })
})
