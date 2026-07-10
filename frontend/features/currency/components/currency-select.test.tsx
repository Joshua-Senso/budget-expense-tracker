import { render, screen } from "@testing-library/react"
import { expect, test, vi } from "vitest"

import { CurrencySelect } from "./currency-select"

test("shows the current value and lets the caller change it", () => {
  const onValueChange = vi.fn()
  const { rerender } = render(<CurrencySelect value="PHP" onValueChange={onValueChange} />)

  expect(screen.getByRole("combobox")).toHaveTextContent("PHP")

  rerender(<CurrencySelect value="USD" onValueChange={onValueChange} />)

  expect(screen.getByRole("combobox")).toHaveTextContent("USD")
})
