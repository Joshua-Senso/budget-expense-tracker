function formatCurrency(amount: string | number, currency: string) {
  const value = typeof amount === "string" ? Number(amount) : amount

  try {
    return new Intl.NumberFormat("en-PH", { style: "currency", currency }).format(value)
  } catch {
    return `${currency} ${value.toFixed(2)}`
  }
}

function formatMonthLabel(year: number, month: number) {
  const date = new Date(Date.UTC(year, month - 1, 1))

  return new Intl.DateTimeFormat("en-PH", {
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(date)
}

function formatMonthName(month: number) {
  const date = new Date(Date.UTC(2000, month - 1, 1))

  return new Intl.DateTimeFormat("en-PH", {
    month: "long",
    timeZone: "UTC",
  }).format(date)
}

function formatExpenseDate(spentOn: string) {
  const date = new Date(`${spentOn}T00:00:00Z`)

  return new Intl.DateTimeFormat("en-PH", {
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  }).format(date)
}

export { formatCurrency, formatMonthLabel, formatMonthName, formatExpenseDate }
