"""Money must be exact, and must refuse to silently mix currencies."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from atlas.domain.money import Converted, Currency, CurrencyMismatchError, FxRate, Money, RateBook

USD, TRY, EUR = Currency("USD"), Currency("TRY"), Currency("EUR")
AT = datetime(2026, 8, 28, 6, 0, tzinfo=UTC)


def test_amount_must_be_decimal_never_float() -> None:
    with pytest.raises(TypeError):
        Money(0.1 + 0.2, USD)  # type: ignore[arg-type]


def test_addition_is_exact() -> None:
    total = Money.of("0.1", "USD") + Money.of("0.2", "USD")
    assert total.amount == Decimal("0.3")


def test_mixing_currencies_raises_rather_than_guessing() -> None:
    with pytest.raises(CurrencyMismatchError):
        Money.of(1, "USD") + Money.of(1, "TRY")


def test_scaling_by_float_is_refused() -> None:
    with pytest.raises(TypeError):
        Money.of(100, "USD") * 1.5  # type: ignore[operator]


@pytest.mark.parametrize("code", ["usd", "US", "USDT", "12A"])
def test_currency_must_be_iso4217(code: str) -> None:
    with pytest.raises(ValueError):
        Currency(code)


def test_ratio_to_rejects_a_zero_denominator() -> None:
    with pytest.raises(ZeroDivisionError):
        Money.of(10, "USD").ratio_to(Money.zero("USD"))


def test_fx_conversion_carries_the_rate_age() -> None:
    book = RateBook((FxRate(TRY, USD, Decimal("0.0245"), AT),))
    result = book.to_base(Money.of(10_000, "TRY"), USD)
    assert isinstance(result, Converted)
    assert result.money.quantize() == Money.of("245.00", "USD")
    assert result.rate_observed_at == AT


def test_same_currency_conversion_introduces_no_rate_age() -> None:
    result = RateBook().to_base(Money.of(5, "USD"), USD)
    assert result is not None
    assert result.rate_observed_at is None


def test_a_missing_rate_returns_none_rather_than_assuming_parity() -> None:
    book = RateBook((FxRate(TRY, USD, Decimal("0.0245"), AT),))
    assert book.to_base(Money.of(5, "EUR"), USD) is None


def test_the_inverse_rate_is_derived_not_assumed() -> None:
    book = RateBook((FxRate(TRY, USD, Decimal("0.02"), AT),))
    back = book.to_base(Money.of(1, "USD"), TRY)
    assert back is not None
    assert back.money.amount == Decimal(50)


def test_a_rate_between_identical_currencies_is_meaningless() -> None:
    with pytest.raises(ValueError):
        FxRate(USD, USD, Decimal(1), AT)


def test_rate_must_carry_an_aware_observation_time() -> None:
    with pytest.raises(ValueError):
        FxRate(TRY, USD, Decimal(1), datetime(2026, 8, 28))
