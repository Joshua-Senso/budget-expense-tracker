import { render, screen } from "@testing-library/react"
import { expect, test } from "vitest"

import Page from "./page"

test("landing page shows product name, features, and sign-in CTA", () => {
  render(<Page />)
  expect(
    screen.getByRole("heading", { name: "Expense Tracker" }),
  ).toBeInTheDocument()
  expect(
    screen.getByRole("link", { name: /sign in to get started/i }),
  ).toHaveAttribute("href", "/sign-in")
  expect(
    screen.getByRole("heading", { name: /multi-currency tracking/i }),
  ).toBeInTheDocument()
})
