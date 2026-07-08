import { act, render, screen } from "@testing-library/react"
import { beforeEach, expect, test, vi } from "vitest"

const themeProviderMock = vi.hoisted(() => ({
  props: vi.fn(),
  setTheme: vi.fn(),
}))

const workspaceThemeMock = vi.hoisted(() => ({
  useWorkspaceTheme: vi.fn(),
}))

vi.mock("next-themes", () => ({
  ThemeProvider: ({ children, ...props }: { children: React.ReactNode }) => {
    themeProviderMock.props(props)
    return <>{children}</>
  },
  useTheme: () => ({ setTheme: themeProviderMock.setTheme }),
}))

vi.mock("@/features/theme", () => ({
  useWorkspaceTheme: workspaceThemeMock.useWorkspaceTheme,
}))

import { ThemeProvider } from "./theme-provider"

beforeEach(() => {
  themeProviderMock.props.mockReset()
  themeProviderMock.setTheme.mockReset()
  workspaceThemeMock.useWorkspaceTheme.mockReset()
  workspaceThemeMock.useWorkspaceTheme.mockReturnValue({
    theme: "dark",
    isPending: false,
    scope: "personal",
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

test("applies the active workspace's stored theme once it resolves", () => {
  workspaceThemeMock.useWorkspaceTheme.mockReturnValue({
    theme: "light",
    isPending: false,
    scope: "household",
  })

  render(
    <ThemeProvider>
      <p>Theme shell</p>
    </ThemeProvider>,
  )

  expect(themeProviderMock.setTheme).toHaveBeenCalledWith("light")
})

test("does not touch the applied theme while the workspace theme is still loading", () => {
  workspaceThemeMock.useWorkspaceTheme.mockReturnValue({
    theme: "dark",
    isPending: true,
    scope: "personal",
  })

  render(
    <ThemeProvider>
      <p>Theme shell</p>
    </ThemeProvider>,
  )

  expect(themeProviderMock.setTheme).not.toHaveBeenCalled()
})

test("re-syncs when the resolved theme changes after a workspace switch", () => {
  const { rerender } = render(
    <ThemeProvider>
      <p>Theme shell</p>
    </ThemeProvider>,
  )
  themeProviderMock.setTheme.mockClear()

  act(() => {
    workspaceThemeMock.useWorkspaceTheme.mockReturnValue({
      theme: "light",
      isPending: false,
      scope: "household",
    })
    rerender(
      <ThemeProvider>
        <p>Theme shell</p>
      </ThemeProvider>,
    )
  })

  expect(themeProviderMock.setTheme).toHaveBeenCalledWith("light")
})
