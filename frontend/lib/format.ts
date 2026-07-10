function formatCurrency(amount: string | number, currency: string) {
  const value = typeof amount === "string" ? Number(amount) : amount

  try {
    // currencyDisplay: "code" shows the ISO code (e.g. "USD 100.00") instead
    // of a symbol -- several supported currencies share an ambiguous "$"
    // symbol (USD, CAD, HKD, SGD, AUD, NZD), so the code is the only way an
    // amount's currency is unambiguous at a glance (PRD §11).
    return new Intl.NumberFormat("en-PH", {
      style: "currency",
      currency,
      currencyDisplay: "code",
    }).format(value)
  } catch {
    return `${currency} ${value.toFixed(2)}`
  }
}

/**
 * Pairs an amount with its base-currency conversion, when one applies.
 * `converted` is null when `currency` already is the base currency, so
 * callers can render a "≈ converted" indicator only when a conversion was
 * actually applied (PRD §11).
 */
function formatConvertedAmount(
  amount: string | number,
  currency: string,
  baseAmount: string | number,
  baseCurrency: string,
): { primary: string; converted: string | null } {
  const primary = formatCurrency(amount, currency)

  if (currency === baseCurrency) {
    return { primary, converted: null }
  }

  return { primary, converted: formatCurrency(baseAmount, baseCurrency) }
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

export {
  formatCurrency,
  formatConvertedAmount,
  formatMonthLabel,
  formatMonthName,
  formatExpenseDate,
}
