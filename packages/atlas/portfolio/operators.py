"""Deterministic portfolio operators (Queue 08).

Every function here is pure: typed in, typed out, no network, no clock, no model. `as_of`
is always passed by the caller (A02, A07), so a live cycle and a historical replay run the
identical code.

Each operator returns a `Measured`, so a gap in the inputs reaches the brief as a named
condition rather than as a plausible number (A06). Three gaps are recognised:

* an unpriced holding — never counted as zero;
* a missing FX rate — never assumed to be parity;
* an observation older than the freshness SLA — the value is still returned, marked stale.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from datetime import datetime, timedelta
from decimal import Decimal

from atlas.domain.measurement import Measured, MeasurementContext, MissingReason
from atlas.domain.money import Currency, Money, RateBook
from atlas.portfolio.holdings import (
    AssetClass,
    CashflowRange,
    Concentration,
    Holding,
    IncomeStream,
    MarkToMarket,
    Shock,
)

DEFAULT_FRESHNESS_SLA = timedelta(hours=24)


def _valued(
    holdings: Iterable[Holding],
    base: Currency,
    rates: RateBook,
    as_of: datetime,
    sla: timedelta,
    ctx: MeasurementContext,
) -> list[tuple[Holding, Money]]:
    """Convert every holding into the base currency, recording each gap it meets."""
    valued: list[tuple[Holding, Money]] = []
    for holding in holdings:
        ctx.observed(holding.observed_at)
        if as_of - holding.observed_at > sla:
            age = (as_of - holding.observed_at).days
            ctx.note(holding.key, MissingReason.STALE, f"{age}d since last observation")
        if not holding.is_priced:
            ctx.note(holding.key, MissingReason.UNKNOWN, "held but not priced")
            continue
        assert holding.market_value is not None
        converted = rates.to_base(holding.market_value, base)
        if converted is None:
            ctx.note(
                f"{holding.currency}/{base}",
                MissingReason.MISSING,
                f"no rate to value {holding.key}",
            )
            continue
        ctx.observed(converted.rate_observed_at)
        valued.append((holding, converted.money))
    return valued


def _total(valued: Iterable[tuple[Holding, Money]], base: Currency) -> Money:
    total = Money.zero(base)
    for _, value in valued:
        total = total + value
    return total


def net_worth(
    holdings: Iterable[Holding],
    *,
    base: Currency,
    rates: RateBook,
    as_of: datetime,
    freshness_sla: timedelta = DEFAULT_FRESHNESS_SLA,
) -> Measured[Money]:
    """Total value of everything Atlas can price, in the base currency."""
    ctx = MeasurementContext()
    valued = _valued(holdings, base, rates, as_of, freshness_sla, ctx)
    if not valued:
        ctx.note("net worth", MissingReason.UNKNOWN, "no holding could be valued")
        return ctx.abandon()
    return ctx.settle(_total(valued, base))


def liquid_net_worth(
    holdings: Iterable[Holding],
    *,
    base: Currency,
    rates: RateBook,
    as_of: datetime,
    freshness_sla: timedelta = DEFAULT_FRESHNESS_SLA,
) -> Measured[Money]:
    """Net worth restricted to holdings the owner could actually reach quickly."""
    return net_worth(
        [h for h in holdings if h.liquid],
        base=base,
        rates=rates,
        as_of=as_of,
        freshness_sla=freshness_sla,
    )


def _weights_by(
    holdings: Iterable[Holding],
    key_of: Callable[[Holding], str],
    *,
    base: Currency,
    rates: RateBook,
    as_of: datetime,
    freshness_sla: timedelta,
) -> Measured[Mapping[str, Decimal]]:
    ctx = MeasurementContext()
    valued = _valued(holdings, base, rates, as_of, freshness_sla, ctx)
    total = _total(valued, base)
    if not valued or total.amount == 0:
        ctx.note("weights", MissingReason.UNKNOWN, "no valued holdings to weigh")
        return ctx.abandon()
    buckets: dict[str, Money] = {}
    for holding, value in valued:
        key = key_of(holding)
        buckets[key] = buckets.get(key, Money.zero(base)) + value
    return ctx.settle({key: amount.ratio_to(total) for key, amount in sorted(buckets.items())})


def currency_weights(
    holdings: Iterable[Holding],
    *,
    base: Currency,
    rates: RateBook,
    as_of: datetime,
    freshness_sla: timedelta = DEFAULT_FRESHNESS_SLA,
) -> Measured[Mapping[str, Decimal]]:
    """Share of value held in each currency. The exposure that FX moves act on."""
    return _weights_by(
        holdings,
        lambda h: str(h.currency),
        base=base,
        rates=rates,
        as_of=as_of,
        freshness_sla=freshness_sla,
    )


def asset_class_weights(
    holdings: Iterable[Holding],
    *,
    base: Currency,
    rates: RateBook,
    as_of: datetime,
    freshness_sla: timedelta = DEFAULT_FRESHNESS_SLA,
) -> Measured[Mapping[str, Decimal]]:
    """Share of value in each asset class."""
    return _weights_by(
        holdings,
        lambda h: str(h.asset_class),
        base=base,
        rates=rates,
        as_of=as_of,
        freshness_sla=freshness_sla,
    )


def geography_weights(
    holdings: Iterable[Holding],
    *,
    base: Currency,
    rates: RateBook,
    as_of: datetime,
    freshness_sla: timedelta = DEFAULT_FRESHNESS_SLA,
) -> Measured[Mapping[str, Decimal]]:
    """Share of value by jurisdiction. Holdings with no geography group as ``unattributed``."""
    return _weights_by(
        holdings,
        lambda h: h.geography or "unattributed",
        base=base,
        rates=rates,
        as_of=as_of,
        freshness_sla=freshness_sla,
    )


def concentration(
    holdings: Iterable[Holding],
    *,
    base: Currency,
    rates: RateBook,
    as_of: datetime,
    freshness_sla: timedelta = DEFAULT_FRESHNESS_SLA,
) -> Measured[Concentration]:
    """Herfindahl concentration over individual holdings.

    ``hhi`` runs from ~0 (perfectly spread) to 1 (everything in one holding), and
    ``effective_holdings`` is its reciprocal — the number of equally-sized holdings that
    would be as concentrated as this portfolio. That reciprocal is the number worth
    showing an owner: "you are as concentrated as if you held 2.4 things".
    """
    ctx = MeasurementContext()
    valued = _valued(holdings, base, rates, as_of, freshness_sla, ctx)
    total = _total(valued, base)
    if not valued or total.amount == 0:
        ctx.note("concentration", MissingReason.UNKNOWN, "no valued holdings")
        return ctx.abandon()

    by_key: dict[str, Money] = {}
    for holding, value in valued:
        by_key[holding.key] = by_key.get(holding.key, Money.zero(base)) + value

    weights = {key: amount.ratio_to(total) for key, amount in by_key.items()}
    hhi = sum((w * w for w in weights.values()), start=Decimal(0))
    largest_key, largest_weight = max(weights.items(), key=lambda kv: kv[1])
    return ctx.settle(
        Concentration(
            hhi=hhi,
            largest_key=largest_key,
            largest_weight=largest_weight,
            effective_holdings=(Decimal(1) / hhi) if hhi > 0 else Decimal(0),
        )
    )


def runway_months(liquid: Measured[Money], monthly_burn: Money) -> Measured[Decimal]:
    """How many months of burn the liquid position covers.

    Takes a `Measured` rather than a bare `Money` so that staleness in the position
    figures propagates into the runway — which is exactly the case the interface must
    show as provisional rather than as a confident number.
    """
    if monthly_burn.amount <= 0:
        raise ValueError("monthly burn must be positive to express a runway")
    if liquid.value is None:
        return Measured[Decimal].unavailable(liquid.missing)
    if liquid.value.currency != monthly_burn.currency:
        raise ValueError("liquid position and burn must share a currency")
    months = liquid.value.ratio_to(monthly_burn)
    return Measured[Decimal](months, liquid.completeness, liquid.missing, liquid.oldest_input_at)


def monthly_cashflow_range(
    incomes: Iterable[IncomeStream],
    monthly_burn: Money,
    *,
    base: Currency,
    rates: RateBook,
) -> Measured[CashflowRange]:
    """Net monthly cashflow across the income range, after burn."""
    if monthly_burn.currency != base:
        raise ValueError("burn must already be expressed in the base currency")
    ctx = MeasurementContext()
    low = mid = high = Money.zero(base)
    counted = 0
    for stream in incomes:
        if not stream.active:
            continue
        ctx.observed(stream.observed_at)
        parts: list[Money] = []
        for amount in (stream.expected_low, stream.expected_base, stream.expected_high):
            converted = rates.to_base(amount, base)
            if converted is None:
                ctx.note(
                    f"{stream.currency}/{base}",
                    MissingReason.MISSING,
                    f"no rate for income stream {stream.key}",
                )
                parts = []
                break
            ctx.observed(converted.rate_observed_at)
            parts.append(converted.money)
        if not parts:
            continue
        low, mid, high = low + parts[0], mid + parts[1], high + parts[2]
        counted += 1

    if counted == 0:
        ctx.note("income", MissingReason.UNKNOWN, "no active income stream could be valued")
        return ctx.abandon()
    return ctx.settle(
        CashflowRange(low=low - monthly_burn, base=mid - monthly_burn, high=high - monthly_burn)
    )


def scenario_mark_to_market(
    holdings: Iterable[Holding],
    shocks: Iterable[Shock],
    *,
    base: Currency,
    rates: RateBook,
    as_of: datetime,
    freshness_sla: timedelta = DEFAULT_FRESHNESS_SLA,
) -> Measured[MarkToMarket]:
    """Revalue the portfolio under proportional per-asset-class shocks.

    Unshocked classes are carried at their current value, not dropped — a scenario that
    silently omitted them would understate the portfolio rather than the move.
    """
    ctx = MeasurementContext()
    valued = _valued(holdings, base, rates, as_of, freshness_sla, ctx)
    if not valued:
        ctx.note("mark to market", MissingReason.UNKNOWN, "no valued holdings")
        return ctx.abandon()

    by_class: dict[AssetClass, Decimal] = {}
    for shock in shocks:
        if shock.asset_class in by_class:
            raise ValueError(f"duplicate shock for {shock.asset_class}")
        by_class[shock.asset_class] = shock.change

    before = _total(valued, base)
    after = Money.zero(base)
    for holding, value in valued:
        change = by_class.get(holding.asset_class, Decimal(0))
        after = after + value * (Decimal(1) + change)

    delta = after - before
    return ctx.settle(
        MarkToMarket(
            before=before,
            after=after,
            change=delta,
            change_fraction=delta.amount / before.amount if before.amount else Decimal(0),
        )
    )
