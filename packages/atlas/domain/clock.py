"""Time access for Atlas.

A02 (time is a first-class dimension) and A07 (same engine for replay and live state)
require that no domain or engine code reads the wall clock directly. Every ``as_of``
value enters the system through a :class:`Clock`, so a live cycle and a historical
replay differ only in which clock and data source are injected.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """Source of the current instant. Always timezone-aware UTC."""

    def now(self) -> datetime: ...


class SystemClock:
    """Live clock. The only sanctioned reader of the wall clock."""

    def now(self) -> datetime:
        return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class FixedClock:
    """Deterministic clock for replay, golden fixtures and unit tests."""

    instant: datetime

    def __post_init__(self) -> None:
        if self.instant.tzinfo is None:
            raise ValueError("FixedClock requires a timezone-aware instant")

    def now(self) -> datetime:
        return self.instant
