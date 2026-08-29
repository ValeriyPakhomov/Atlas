"""Exact money arithmetic.

Money is never a float and never implicitly convertible. Adding USD to TRY raises
rather than producing a plausible number, and converting requires an `FxRate` that
carries its own observation time — so a currency-weight calculation cannot quietly
use a rate from last month (A02, A06).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Self


class CurrencyMismatchError(ValueError):
    """Raised when an operation would combine two different currencies."""


@dataclass(frozen=True, slots=True, order=True)
class Currency:
    """An ISO 4217 alphabetic code."""

    code: str

    def __post_init__(self) -> None:
        if len(self.code) != 3 or not self.code.isalpha() or not self.code.isupper():
            raise ValueError("currency must be a 3-letter uppercase ISO 4217 code")

    def __str__(self) -> str:
        return self.code


@dataclass(frozen=True, slots=True)
class Money:
    """An exact amount in one currency."""

    amount: Decimal
    currency: Currency

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise TypeError("amount must be a Decimal — never a float")
        if not self.amount.is_finite():
            raise ValueError("amount must be finite")

    @classmethod
    def of(cls, amount: str | int | Decimal, currency: str | Currency) -> Self:
        """Build from a string or int. Deliberately no float overload."""
        code = currency if isinstance(currency, Currency) else Currency(currency)
        return cls(Decimal(amount), code)

    @classmethod
    def zero(cls, currency: str | Currency) -> Self:
        return cls.of(0, currency)

    def _same(self, other: Money) -> None:
        if self.currency != other.currency:
            raise CurrencyMismatchError(
                f"cannot combine {self.currency} and {other.currency} without an FxRate"
            )

    def __add__(self, other: Money) -> Money:
        self._same(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._same(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: Decimal | int) -> Money:
        if isinstance(factor, float):
            raise TypeError("cannot scale Money by a float — use Decimal")
        return Money(self.amount * Decimal(factor), self.currency)

    __rmul__ = __mul__

    def __neg__(self) -> Money:
        return Money(-self.amount, self.currency)

    def __lt__(self, other: Money) -> bool:
        self._same(other)
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        self._same(other)
        return self.amount <= other.amount

    def ratio_to(self, other: Money) -> Decimal:
        """This amount as a fraction of another. Same currency only."""
        self._same(other)
        if other.amount == 0:
            raise ZeroDivisionError("cannot express a ratio to a zero denominator")
        return self.amount / other.amount

    @property
    def is_positive(self) -> bool:
        return self.amount > 0

    def quantize(self, places: int = 2) -> Money:
        """Round for display only. Never used inside a calculation chain."""
        exp = Decimal(1).scaleb(-places)
        return Money(self.amount.quantize(exp, rounding=ROUND_HALF_EVEN), self.currency)

    def __str__(self) -> str:
        return f"{self.quantize().amount} {self.currency}"


@dataclass(frozen=True, slots=True)
class Converted:
    """A converted amount, plus the age of the rate that produced it.

    ``rate_observed_at`` is ``None`` when the holding was already in the base
    currency, so no FX staleness was introduced.
    """

    money: Money
    rate_observed_at: datetime | None


@dataclass(frozen=True, slots=True)
class FxRate:
    """One unit of `base` expressed in `quote`, observed at a point in time."""

    base: Currency
    quote: Currency
    rate: Decimal
    observed_at: datetime

    def __post_init__(self) -> None:
        if self.base == self.quote:
            raise ValueError("an FX rate needs two different currencies")
        if self.rate <= 0:
            raise ValueError("rate must be positive")
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")

    def invert(self) -> FxRate:
        return FxRate(self.quote, self.base, Decimal(1) / self.rate, self.observed_at)

    def convert(self, money: Money) -> Money:
        if money.currency != self.base:
            raise CurrencyMismatchError(
                f"rate converts from {self.base}, not from {money.currency}"
            )
        return Money(money.amount * self.rate, self.quote)


class RateBook:
    """The rates available for one conversion pass, with their observation times.

    Deliberately not a dict lookup with a silent default: a missing rate is a
    *reported* gap, not a zero and not an assumed parity (A06).
    """

    __slots__ = ("_rates",)

    def __init__(self, rates: tuple[FxRate, ...] = ()) -> None:
        index: dict[tuple[Currency, Currency], FxRate] = {}
        for rate in rates:
            index[(rate.base, rate.quote)] = rate
            index.setdefault((rate.quote, rate.base), rate.invert())
        self._rates = index

    def find(self, base: Currency, quote: Currency) -> FxRate | None:
        if base == quote:
            return None
        return self._rates.get((base, quote))

    def to_base(self, money: Money, base: Currency) -> Converted | None:
        """Convert into the base currency.

        Returns ``None`` when no rate is available — callers must surface that as a
        named missing input rather than dropping the holding or assuming parity.
        """
        if money.currency == base:
            return Converted(money, None)
        rate = self.find(money.currency, base)
        if rate is None:
            return None
        return Converted(rate.convert(money), rate.observed_at)
