export const SUPPORTED_CURRENCIES = [
  "AED",
  "AUD",
  "CAD",
  "CHF",
  "CNY",
  "EUR",
  "GBP",
  "HKD",
  "IDR",
  "INR",
  "JPY",
  "KRW",
  "MYR",
  "NZD",
  "PHP",
  "SAR",
  "SGD",
  "THB",
  "USD",
  "VND",
] as const

export type CurrencyCode = (typeof SUPPORTED_CURRENCIES)[number]

export const DEFAULT_CURRENCY: CurrencyCode = "PHP"
