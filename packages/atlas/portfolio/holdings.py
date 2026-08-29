"""Inputs to the deterministic portfolio operators (Queue 08).

`Holding` deliberately unifies a position and a cash balance. The operators care about
value, currency, asset class, liquidity and freshness — not about which table a row came
from. Persistence keeps `Position` and `CashBalance` separate; this is the shape the
arithmetic actually needs, and collapsing it here keeps every operator single-path.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from atlas.domain.money import Currency, Money


class AssetClass(StrEnum):
    CASH = "cash"
    CRYPTO = "crypto"
    EQUITY = "equity"
    FIXED_INCOME = "fixed_income"
    REAL_ASSET = "real_asset"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class Holding:
    """One valued position or cash balance at a point in time."""

    key: str
    asset_class: AssetClass
    currency: Currency
    observed_at: datetime
    market_value: Money | None = None
    liquid: bool = True
    geography: str | None = None
    account_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("a holding must have a key")
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        if self.market_value is not None and self.market_value.currency != self.currency:
            raise ValueError("market_value currency must match the holding currency")

    @property
    def is_priced(self) -> bool:
        """False when Atlas holds the position but could not value it.

        An unpriced holding is never treated as zero — that is the specific A06
        failure the missing-data tests exist to catch.
        """
        return self.market_value is not None


@dataclass(frozen=True, slots=True)
class IncomeStream:
    """An expected monthly income range, in its own currency."""

    key: str
    currency: Currency
    expected_low: Money
    expected_base: Money
    expected_high: Money
    confidence: Decimal
    active: bool = True
    mobility_dependent: bool = False
    observed_at: datetime | None = None

    def __post_init__(self) -> None:
        for label, value in (
            ("expected_low", self.expected_low),
            ("expected_base", self.expected_base),
            ("expected_high", self.expected_high),
        ):
            if value.currency != self.currency:
                raise ValueError(f"{label} currency must match the stream currency")
        if not (self.expected_low <= self.expected_base <= self.expected_high):
            raise ValueError("income range must be ordered low <= base <= high")
        if not Decimal(0) <= self.confidence <= Decimal(1):
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class Shock:
    """A proportional move applied to one asset class in a scenario.

    ``-0.20`` means a 20% fall. Expressed as a fraction rather than a new price so the
    same shock applies to a portfolio of any size.
    """

    asset_class: AssetClass
    change: Decimal

    def __post_init__(self) -> None:
        if self.change <= Decimal(-1):
            raise ValueError("a shock cannot remove more than the whole position")


@dataclass(frozen=True, slots=True)
class Concentration:
    """How concentrated a portfolio is, by the Herfindahl index over holdings."""

    hhi: Decimal
    largest_key: str
    largest_weight: Decimal
    effective_holdings: Decimal


@dataclass(frozen=True, slots=True)
class CashflowRange:
    """Monthly net cashflow across the income range, against a fixed burn."""

    low: Money
    base: Money
    high: Money


@dataclass(frozen=True, slots=True)
class MarkToMarket:
    """A portfolio revalued under a scenario."""

    before: Money
    after: Money
    change: Money
    change_fraction: Decimal
