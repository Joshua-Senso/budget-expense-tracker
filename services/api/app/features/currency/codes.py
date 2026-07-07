"""Canonical currency codes the app accepts (PRD §7.10)."""

DEFAULT_CURRENCY = "PHP"

SUPPORTED_CURRENCIES: frozenset[str] = frozenset(
    {
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
    }
)
