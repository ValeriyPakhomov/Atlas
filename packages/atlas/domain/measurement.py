"""A06 expressed as a type.

Every deterministic operator returns a ``Measured`` rather than a bare number. You
cannot get a value out without acknowledging how complete it is, and you cannot lose
the reason a number is incomplete — the gaps travel with the result all the way to
the brief, where the interface renders them as ``STALE`` / ``UNKNOWN`` / ``CONFLICTING``
instead of showing a plausible figure.

The rule that makes this work: **incompleteness propagates**. Combining a complete
value with a partial one yields a partial result carrying both sets of gaps, and the
freshness of a derived value is the freshness of its *oldest* input.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Self


class Completeness(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class MissingReason(StrEnum):
    UNKNOWN = "unknown"
    STALE = "stale"
    MISSING = "missing"
    CONFLICTING = "conflicting"
    UNVERIFIED = "unverified"


class IncompleteResultError(RuntimeError):
    """Raised by ``require()`` when a caller demands a value Atlas does not have."""


@dataclass(frozen=True, slots=True, order=True)
class MissingInput:
    """One named gap. Rendered directly by the interface, so the text is user-facing."""

    subject: str
    reason: MissingReason
    detail: str = ""

    def __post_init__(self) -> None:
        if not self.subject.strip():
            raise ValueError("a missing input must name its subject")

    def __str__(self) -> str:
        return f"{self.subject}: {self.reason}" + (f" — {self.detail}" if self.detail else "")


@dataclass(frozen=True, slots=True)
class Measured[T]:
    """A computed value together with what Atlas did not know while computing it."""

    value: T | None
    completeness: Completeness
    missing: tuple[MissingInput, ...] = ()
    oldest_input_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.completeness is Completeness.UNAVAILABLE and self.value is not None:
            raise ValueError("an unavailable result cannot carry a value")
        if self.completeness is not Completeness.UNAVAILABLE and self.value is None:
            raise ValueError("only an unavailable result may omit its value")
        if self.completeness is Completeness.COMPLETE and self.missing:
            raise ValueError("a complete result cannot name missing inputs")
        if self.completeness is not Completeness.COMPLETE and not self.missing:
            raise ValueError("an incomplete result must say what is missing")

    # ── constructors ────────────────────────────────────────────────────────
    @classmethod
    def complete(cls, value: T, *, oldest_input_at: datetime | None = None) -> Self:
        return cls(value, Completeness.COMPLETE, (), oldest_input_at)

    @classmethod
    def partial(
        cls,
        value: T,
        missing: Iterable[MissingInput],
        *,
        oldest_input_at: datetime | None = None,
    ) -> Self:
        return cls(value, Completeness.PARTIAL, _dedupe(missing), oldest_input_at)

    @classmethod
    def unavailable(cls, missing: Iterable[MissingInput]) -> Self:
        return cls(None, Completeness.UNAVAILABLE, _dedupe(missing), None)

    # ── access ──────────────────────────────────────────────────────────────
    @property
    def is_usable(self) -> bool:
        """True when a value exists, even if some inputs were missing."""
        return self.value is not None

    def require(self) -> T:
        """Return the value, or raise. Use only where a partial answer is unsafe."""
        if self.completeness is not Completeness.COMPLETE:
            raise IncompleteResultError(
                "result is "
                + self.completeness
                + "; missing "
                + ", ".join(str(m) for m in self.missing)
            )
        assert self.value is not None
        return self.value

    def or_else(self, fallback: T) -> T:
        """Explicit, visible fallback. Never call this to paper over a gap in a brief."""
        return self.value if self.value is not None else fallback

    # ── composition ─────────────────────────────────────────────────────────
    def map[U](self, fn: Callable[[T], U]) -> Measured[U]:
        """Transform the value, carrying gaps and freshness through unchanged."""
        if self.value is None:
            return Measured[U](None, Completeness.UNAVAILABLE, self.missing, None)
        return Measured[U](fn(self.value), self.completeness, self.missing, self.oldest_input_at)

    def degraded_by(self, missing: Iterable[MissingInput]) -> Measured[T]:
        """Add gaps to an existing result, downgrading COMPLETE to PARTIAL."""
        extra = _dedupe(missing)
        if not extra:
            return self
        if self.value is None:
            return Measured[T](None, Completeness.UNAVAILABLE, _dedupe(self.missing + extra), None)
        return Measured[T](
            self.value,
            Completeness.PARTIAL,
            _dedupe(self.missing + extra),
            self.oldest_input_at,
        )


@dataclass(slots=True)
class MeasurementContext:
    """Accumulates gaps and input ages while an operator runs.

    Operators build a result by recording every gap they meet rather than returning
    early, so the brief can list *all* of what is missing instead of only the first.
    """

    missing: list[MissingInput] = field(default_factory=list)
    oldest_input_at: datetime | None = None

    def note(self, subject: str, reason: MissingReason, detail: str = "") -> None:
        self.missing.append(MissingInput(subject, reason, detail))

    def observed(self, at: datetime | None) -> None:
        if at is None:
            return
        if self.oldest_input_at is None or at < self.oldest_input_at:
            self.oldest_input_at = at

    def absorb[T](self, other: Measured[T]) -> None:
        """Fold another result's gaps and freshness into this computation."""
        self.missing.extend(other.missing)
        self.observed(other.oldest_input_at)

    def settle[T](self, value: T) -> Measured[T]:
        """Close the computation: complete when nothing was missing, else partial."""
        if not self.missing:
            return Measured[T].complete(value, oldest_input_at=self.oldest_input_at)
        return Measured[T].partial(value, self.missing, oldest_input_at=self.oldest_input_at)

    def abandon[T](self) -> Measured[T]:
        """Close the computation with no value at all."""
        if not self.missing:
            raise ValueError("cannot abandon a computation without naming a reason")
        return Measured[T].unavailable(self.missing)


def _dedupe(items: Iterable[MissingInput]) -> tuple[MissingInput, ...]:
    seen: dict[tuple[str, str], MissingInput] = {}
    for item in items:
        seen.setdefault((item.subject, str(item.reason)), item)
    return tuple(seen.values())
