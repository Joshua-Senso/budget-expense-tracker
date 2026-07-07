from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.features.exchange_rates.schemas import ExchangeRateUpsert


class TestExchangeRateUpsertCurrency:
    def test_uppercases_and_strips(self) -> None:
        schema = ExchangeRateUpsert(
            from_currency=" usd ", to_currency="php", rate=Decimal("56.00")
        )
        assert schema.from_currency == "USD"
        assert schema.to_currency == "PHP"

    def test_unsupported_currency_raises(self) -> None:
        with pytest.raises(ValidationError):
            ExchangeRateUpsert(
                from_currency="XXX", to_currency="PHP", rate=Decimal("56.00")
            )

    def test_same_currency_pair_raises(self) -> None:
        with pytest.raises(ValidationError):
            ExchangeRateUpsert(
                from_currency="PHP", to_currency="PHP", rate=Decimal("1")
            )


class TestExchangeRateUpsertRate:
    def test_positive_rate_accepted(self) -> None:
        schema = ExchangeRateUpsert(
            from_currency="USD", to_currency="PHP", rate=Decimal("56.00")
        )
        assert schema.rate == Decimal("56.00")

    def test_zero_rate_raises(self) -> None:
        with pytest.raises(ValidationError):
            ExchangeRateUpsert(
                from_currency="USD", to_currency="PHP", rate=Decimal("0")
            )

    def test_negative_rate_raises(self) -> None:
        with pytest.raises(ValidationError):
            ExchangeRateUpsert(
                from_currency="USD", to_currency="PHP", rate=Decimal("-1")
            )
