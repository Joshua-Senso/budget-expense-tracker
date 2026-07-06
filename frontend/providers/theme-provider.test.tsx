import { act, render, screen } from "@testing-library/react"
import { beforeEach, expect, test, vi } from "vitest"

import { useWorkspaceStore } from "@/stores/workspace-store"

const themeProviderMock = vi.hoisted(() => ({
  props: vi.fn(),
  setTheme: vi.fn(),
  resolvedTheme: "dark",
}))

vi.mock("next-themes", () => ({
  ThemeProvider: ({ children, ...props }: { children: React.ReactNode }) => {
    themeProviderMock.props(props)
    return <>{children}</>
  },
  useTheme: () => ({
    resolvedTheme: themeProviderMock.resolvedTheme,
    setTheme: themeProviderMock.setTheme,
  }),
}))

import { ThemeProvider } from "./theme-provider"

beforeEach(() => {
  themeProviderMock.props.mockReset()
  themeProviderMock.setTheme.mockReset()
  themeProviderMock.resolvedTheme = "dark"
  localStorage.clear()
  useWorkspaceStore.setState({
    activeWorkspaceId: null,
    activeWorkspaceScope: "personal",
  })
})

test("theme provider defaults to warm dark instead of system", () => {
  render(
    <ThemeProvider>
      <p>Theme shell</p>
    </ThemeProvider>,
  )

  expect(screen.getByText("Theme shell")).toBeInTheDocument()
  expect(themeProviderMock.props).toHaveBeenCalledWith(
    expect.objectContaining({
      attribute: "class",
      defaultTheme: "dark",
      enableSystem: false,
    }),
  )
})

test("applies the active workspace's saved theme when switching workspaces", () => {
  localStorage.setItem(
    "workspace-themes",
    JSON.stringify({ "household:house-1": "light" }),
  )

  render(
    <ThemeProvider>
      <p>Theme shell</p>
    </ThemeProvider>,
  )
  themeProviderMock.setTheme.mockClear()

  act(() => {
    useWorkspaceStore.getState().setActiveWorkspace({ id: "house-1" })
  })

  expect(themeProviderMock.setTheme).toHaveBeenCalledWith("light")
})

test("falls back to the default theme for a workspace with no saved preference", () => {
  render(
    <ThemeProvider>
      <p>Theme shell</p>
    </ThemeProvider>,
  )
  themeProviderMock.setTheme.mockClear()

  act(() => {
    useWorkspaceStore.getState().setActiveWorkspace({ id: "house-2" })
  })

  expect(themeProviderMock.setTheme).toHaveBeenCalledWith("dark")
})

test("persists the hotkey toggle under the active workspace", () => {
  useWorkspaceStore.setState({
    activeWorkspaceId: "house-1",
    activeWorkspaceScope: "household",
  })

  render(
    <ThemeProvider>
      <p>Theme shell</p>
    </ThemeProvider>,
  )

  window.dispatchEvent(new KeyboardEvent("keydown", { key: "d" }))

  expect(themeProviderMock.setTheme).toHaveBeenCalledWith("light")
  expect(JSON.parse(localStorage.getItem("workspace-themes") ?? "{}")).toMatchObject({
    "household:house-1": "light",
  })
})

test("keeps the hotkey toggle scoped to personal when no household is active", () => {
  render(
    <ThemeProvider>
      <p>Theme shell</p>
    </ThemeProvider>,
  )

  window.dispatchEvent(new KeyboardEvent("keydown", { key: "d" }))

  expect(JSON.parse(localStorage.getItem("workspace-themes") ?? "{}")).toMatchObject({
    personal: "light",
  })
})
