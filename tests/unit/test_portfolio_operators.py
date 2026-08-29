"""Queue 08 operators. The missing-data cases matter more than the arithmetic ones."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from atlas.domain.measurement import (
    Completeness,
    IncompleteResultError,
    Measured,
    MissingReason,
)
from atlas.domain.money import Currency, FxRate, Money, RateBook
from atlas.portfolio.holdings import AssetClass, Holding, IncomeStream, Shock
from atlas.portfolio.operators import (
    asset_class_weights,
    concentration,
    currency_weights,
    liquid_net_worth,
    monthly_cashflow_range,
    net_worth,
    runway_months,
    scenario_mark_to_market,
)

USD, TRY = Currency("USD"), Currency("TRY")
NOW = datetime(2026, 8, 28, 9, 0, tzinfo=UTC)
FRESH = NOW - timedelta(hours=2)
STALE = NOW - timedelta(days=9)
RATES = RateBook((FxRate(TRY, USD, Decimal("0.0245"), FRESH),))


def holding(key: str, value: str | None, **kw: object) -> Holding:
    currency = kw.pop("currency", USD)
    assert isinstance(currency, Currency)
    return Holding(
        key=key,
        asset_class=kw.pop("asset_class", AssetClass.CRYPTO),  # type: ignore[arg-type]
        currency=currency,
        observed_at=kw.pop("observed_at", FRESH),  # type: ignore[arg-type]
        market_value=Money.of(value, currency) if value is not None else None,
        liquid=bool(kw.pop("liquid", True)),
        geography=kw.pop("geography", None),  # type: ignore[arg-type]
    )


def measured(amount: str) -> Measured[Money]:
    return Measured.complete(Money.of(amount, "USD"))


# ── arithmetic ──────────────────────────────────────────────────────────────
def test_net_worth_sums_across_currencies_via_explicit_rates() -> None:
    result = net_worth(
        [holding("btc", "100000"), holding("try-cash", "10000", currency=TRY)],
        base=USD,
        rates=RATES,
        as_of=NOW,
    )
    assert result.completeness is Completeness.COMPLETE
    assert result.require().quantize() == Money.of("100245.00", "USD")


def test_liquid_net_worth_excludes_illiquid_holdings() -> None:
    holdings = [holding("cash", "50000"), holding("property", "300000", liquid=False)]
    assert liquid_net_worth(holdings, base=USD, rates=RATES, as_of=NOW).require() == Money.of(
        50000, "USD"
    )


def test_currency_weights_sum_to_one() -> None:
    weights = currency_weights(
        [holding("a", "75000"), holding("b", "25000")], base=USD, rates=RATES, as_of=NOW
    ).require()
    assert sum(weights.values()) == Decimal(1)
    assert weights["USD"] == Decimal(1)


def test_asset_class_weights_group_by_class() -> None:
    weights = asset_class_weights(
        [
            holding("btc", "60000"),
            holding("cash", "40000", asset_class=AssetClass.CASH),
        ],
        base=USD,
        rates=RATES,
        as_of=NOW,
    ).require()
    assert weights["crypto"] == Decimal("0.6")
    assert weights["cash"] == Decimal("0.4")


def test_concentration_reports_effective_holdings() -> None:
    result = concentration(
        [holding("a", "50000"), holding("b", "50000")], base=USD, rates=RATES, as_of=NOW
    ).require()
    assert result.hhi == Decimal("0.5")
    assert result.effective_holdings == Decimal(2)
    assert result.largest_weight == Decimal("0.5")


def test_a_single_holding_is_maximally_concentrated() -> None:
    result = concentration([holding("btc", "100")], base=USD, rates=RATES, as_of=NOW).require()
    assert result.hhi == Decimal(1)
    assert result.largest_key == "btc"


def test_runway_is_liquid_over_burn() -> None:
    assert runway_months(measured("70000"), Money.of(5000, "USD")).require() == Decimal(14)


def test_runway_refuses_a_non_positive_burn() -> None:
    with pytest.raises(ValueError, match="positive"):
        runway_months(measured("70000"), Money.zero("USD"))


def test_runway_refuses_to_mix_currencies() -> None:
    with pytest.raises(ValueError, match="currency"):
        runway_months(measured("70000"), Money.of(5000, "TRY"))


def test_cashflow_range_is_income_after_burn() -> None:
    stream = IncomeStream(
        key="contract",
        currency=USD,
        expected_low=Money.of(3000, "USD"),
        expected_base=Money.of(5000, "USD"),
        expected_high=Money.of(7000, "USD"),
        confidence=Decimal("0.7"),
    )
    result = monthly_cashflow_range(
        [stream], Money.of(4900, "USD"), base=USD, rates=RATES
    ).require()
    assert result.low == Money.of(-1900, "USD")
    assert result.high == Money.of(2100, "USD")


def test_mark_to_market_shocks_only_the_named_class() -> None:
    result = scenario_mark_to_market(
        [holding("btc", "60000"), holding("cash", "40000", asset_class=AssetClass.CASH)],
        [Shock(AssetClass.CRYPTO, Decimal("-0.20"))],
        base=USD,
        rates=RATES,
        as_of=NOW,
    ).require()
    assert result.after == Money.of(88000, "USD")
    assert result.change == Money.of(-12000, "USD")
    assert result.change_fraction == Decimal("-0.12")


def test_duplicate_shocks_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        scenario_mark_to_market(
            [holding("btc", "1")],
            [Shock(AssetClass.CRYPTO, Decimal("-0.1")), Shock(AssetClass.CRYPTO, Decimal("-0.2"))],
            base=USD,
            rates=RATES,
            as_of=NOW,
        )


# ── A06: missing data must never become a plausible number ──────────────────
def test_an_unpriced_holding_is_named_never_counted_as_zero() -> None:
    result = net_worth(
        [holding("btc", "100000"), holding("art", None)], base=USD, rates=RATES, as_of=NOW
    )
    assert result.completeness is Completeness.PARTIAL
    assert result.value == Money.of(100000, "USD")
    assert [m.subject for m in result.missing] == ["art"]
    assert result.missing[0].reason is MissingReason.UNKNOWN


def test_a_missing_rate_is_named_never_assumed_to_be_parity() -> None:
    result = net_worth(
        [holding("usd", "1000"), holding("eur", "1000", currency=Currency("EUR"))],
        base=USD,
        rates=RATES,
        as_of=NOW,
    )
    assert result.completeness is Completeness.PARTIAL
    assert result.value == Money.of(1000, "USD")
    assert result.missing[0].subject == "EUR/USD"


def test_a_stale_holding_still_returns_a_value_but_marked_stale() -> None:
    result = net_worth(
        [holding("btc", "100000", observed_at=STALE)], base=USD, rates=RATES, as_of=NOW
    )
    assert result.completeness is Completeness.PARTIAL
    assert result.value == Money.of(100000, "USD")
    assert result.missing[0].reason is MissingReason.STALE
    assert "9d" in result.missing[0].detail


def test_staleness_propagates_from_positions_into_runway() -> None:
    liquid = liquid_net_worth(
        [holding("btc", "70000", observed_at=STALE)], base=USD, rates=RATES, as_of=NOW
    )
    runway = runway_months(liquid, Money.of(5000, "USD"))
    assert runway.value == Decimal(14)
    assert runway.completeness is Completeness.PARTIAL
    assert runway.missing[0].reason is MissingReason.STALE


def test_nothing_valuable_yields_no_number_at_all() -> None:
    result = net_worth([holding("art", None)], base=USD, rates=RATES, as_of=NOW)
    assert result.completeness is Completeness.UNAVAILABLE
    assert result.value is None
    with pytest.raises(IncompleteResultError):
        result.require()


def test_runway_on_an_unavailable_position_stays_unavailable() -> None:
    unavailable = net_worth([holding("art", None)], base=USD, rates=RATES, as_of=NOW)
    runway = runway_months(unavailable, Money.of(5000, "USD"))
    assert runway.completeness is Completeness.UNAVAILABLE
    assert runway.missing


def test_freshness_of_a_derived_value_is_its_oldest_input() -> None:
    result = net_worth(
        [holding("a", "1", observed_at=STALE), holding("b", "1")],
        base=USD,
        rates=RATES,
        as_of=NOW,
    )
    assert result.oldest_input_at == STALE
