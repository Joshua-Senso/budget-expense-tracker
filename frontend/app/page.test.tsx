import { render, screen } from "@testing-library/react"
import { expect, test } from "vitest"

import Page from "./page"

test("coming soon page shows the product name and status", () => {
  render(<Page />)
  expect(
    screen.getByRole("heading", { name: "Expense Tracker" }),
  ).toBeInTheDocument()
  expect(screen.getByText("Coming soon")).toBeInTheDocument()
})
