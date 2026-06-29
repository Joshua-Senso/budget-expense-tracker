import { render, screen } from "@testing-library/react"
import { expect, test, vi } from "vitest"

const themeProviderMock = vi.hoisted(() => ({
  props: vi.fn(),
}))

vi.mock("next-themes", () => ({
  ThemeProvider: ({ children, ...props }: { children: React.ReactNode }) => {
    themeProviderMock.props(props)
    return <>{children}</>
  },
  useTheme: () => ({
    resolvedTheme: "dark",
    setTheme: vi.fn(),
  }),
}))

import { ThemeProvider } from "./theme-provider"

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
