"""What Atlas is allowed to read, declared as data.

Open economic data is genuinely open: central banks, statistical agencies and
multilateral institutions publish the series that *define* the macro picture, under terms
that permit exactly this use. That is the backbone. News is the other half, and it plays a
different role — which is the one rule this module enforces as a type invariant:

    **Series move state. News moves attention.**

A measured series is a number with a publisher, a vintage and a revision history; it can
change a world-state dimension deterministically. Reporting is an account of something,
written by someone, with an angle. It can raise a question, name an entity, start a
research task — but if reporting could move a dimension score on its own, the "state of
the economy" would quietly become the *mood of the press about* the economy, which is a
different and much worse quantity. :attr:`SourceSpec.may_move_state` is derived, not
configurable, so no catalogue entry can opt into being both.

The catalogue is deliberately small. Six well-chosen feeds that Atlas can explain beat
sixty it cannot, and every entry added is a permanent maintenance obligation.

**Scope.** This is a declaration, not a client. Nothing here performs I/O; the endpoints
are recorded so an adapter has one place to read them from, and each adapter lands with
its own queue item.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import StrEnum

from atlas.domain.sensitivity import SensitivityTier
from atlas.scoring.relevance import SourceClass


class SourceKind(StrEnum):
    """What a source produces, which decides what it is allowed to do."""

    SERIES = "series"
    """Measured numeric observations with vintages — the only true state input."""

    RELEASE = "release"
    """A scheduled official publication: a rate decision, a filing, a statistical print."""

    MARKET = "market"
    """Prices and quotes. Measured, but continuous and unrevised."""

    NEWS = "news"
    """Reporting. Evidence about the world, never a measurement of it."""

    SIGNAL = "signal"
    """Coverage and attention metrics. Tells Atlas where to look, never what is true."""


class AccessMode(StrEnum):
    OPEN = "open"
    """No credential at all."""

    FREE_KEY = "free_key"
    """A free registration key. The key is a secret and lives only in the environment."""

    ACCOUNT = "account"
    """Requires an account, and usually a paid tier. Not V1."""


class VerificationStatus(StrEnum):
    """Whether the entry has been checked against the live service.

    Recorded rather than assumed. Feed availability and terms change, and an adapter
    written against an unverified entry is a bug waiting for a deploy.
    """

    CONFIRMED = "confirmed"
    NEEDS_CHECK = "needs_check"


@dataclass(frozen=True, slots=True)
class SourceSpec:
    """One source Atlas may read, with the terms it is read under."""

    key: str
    name: str
    publisher: str
    kind: SourceKind
    source_class: SourceClass
    access: AccessMode
    endpoint: str
    latency_class: str
    terms: str
    jurisdiction: str | None = None
    verification: VerificationStatus = VerificationStatus.NEEDS_CHECK
    default_tier: SensitivityTier = SensitivityTier.L0
    notes: str = ""

    def __post_init__(self) -> None:
        for name in ("key", "name", "publisher", "endpoint", "latency_class", "terms"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{self.key or '<unkeyed>'}: {name} is required")
        if not self.endpoint.startswith("https://"):
            raise ValueError(f"{self.key}: endpoint must be https")
        if self.default_tier.rank > SensitivityTier.L1.rank:
            raise ValueError(
                f"{self.key}: public world sources are L0/L1; an L2+ classification here "
                "would mean owner data had been mixed into a world source"
            )
        if self.kind is SourceKind.SIGNAL and self.source_class in {SourceClass.A, SourceClass.B}:
            raise ValueError(
                f"{self.key}: a coverage signal is not a reliable source about the world, "
                "however reliable the platform reporting it"
            )

    @property
    def may_move_state(self) -> bool:
        """Whether this source can change a world-state dimension on its own.

        Derived from kind and class, never declared. Reporting — at any reliability
        class — contributes evidence and narrative, and stops there (A04, `SOURCE_POLICY`).
        """
        return self.kind in {SourceKind.SERIES, SourceKind.RELEASE, SourceKind.MARKET} and (
            self.source_class in {SourceClass.A, SourceClass.B}
        )

    @property
    def needs_credential(self) -> bool:
        return self.access is not AccessMode.OPEN


# ── the catalogue ───────────────────────────────────────────────────────────────
#
# Endpoints are documented entry points, recorded so adapters have one place to read them
# from. Nothing here has been contacted; ``verification`` says which entries have been
# checked against the live service, and an adapter may not ship against NEEDS_CHECK.

MACRO_SERIES: tuple[SourceSpec, ...] = (
    SourceSpec(
        key="fred",
        name="FRED economic series",
        publisher="Federal Reserve Bank of St. Louis",
        kind=SourceKind.SERIES,
        source_class=SourceClass.A,
        access=AccessMode.FREE_KEY,
        endpoint="https://api.stlouisfed.org/fred",
        latency_class="daily",
        jurisdiction="US",
        terms="Free API with a registration key; redistribution of series data is limited.",
        notes="Backbone for rates, liquidity, USD, inflation and credit spreads.",
    ),
    SourceSpec(
        key="ecb_data",
        name="ECB Data Portal",
        publisher="European Central Bank",
        kind=SourceKind.SERIES,
        source_class=SourceClass.A,
        access=AccessMode.OPEN,
        endpoint="https://data-api.ecb.europa.eu/service",
        latency_class="daily",
        jurisdiction="EU",
        terms="Open SDMX REST API, no key.",
    ),
    SourceSpec(
        key="eurostat",
        name="Eurostat statistics",
        publisher="European Commission",
        kind=SourceKind.SERIES,
        source_class=SourceClass.A,
        access=AccessMode.OPEN,
        endpoint="https://ec.europa.eu/eurostat/api/dissemination",
        latency_class="monthly",
        jurisdiction="EU",
        terms="Open data, attribution required.",
    ),
    SourceSpec(
        key="worldbank",
        name="World Bank indicators",
        publisher="World Bank",
        kind=SourceKind.SERIES,
        source_class=SourceClass.A,
        access=AccessMode.OPEN,
        endpoint="https://api.worldbank.org/v2",
        latency_class="annual",
        terms="Open data licence (CC BY 4.0 for most indicators).",
        notes="Slow-moving country context, not a daily input.",
    ),
    SourceSpec(
        key="imf",
        name="IMF data",
        publisher="International Monetary Fund",
        kind=SourceKind.SERIES,
        source_class=SourceClass.A,
        access=AccessMode.OPEN,
        endpoint="https://www.imf.org/external/datamapper/api/v1",
        latency_class="quarterly",
        terms="Open for non-commercial use with attribution.",
    ),
    SourceSpec(
        key="us_treasury_fiscal",
        name="US Treasury fiscal data",
        publisher="US Department of the Treasury",
        kind=SourceKind.SERIES,
        source_class=SourceClass.A,
        access=AccessMode.OPEN,
        endpoint="https://api.fiscaldata.treasury.gov/services/api/fiscal_service",
        latency_class="daily",
        jurisdiction="US",
        terms="US Government work, public domain.",
        notes="Yield curve and issuance, independent of FRED's availability.",
    ),
    SourceSpec(
        key="eia",
        name="EIA energy data",
        publisher="US Energy Information Administration",
        kind=SourceKind.SERIES,
        source_class=SourceClass.A,
        access=AccessMode.FREE_KEY,
        endpoint="https://api.eia.gov/v2",
        latency_class="weekly",
        jurisdiction="US",
        terms="US Government work, public domain; free API key.",
    ),
)

OFFICIAL_RELEASES: tuple[SourceSpec, ...] = (
    SourceSpec(
        key="federal_reserve_press",
        name="Federal Reserve press releases",
        publisher="Board of Governors of the Federal Reserve System",
        kind=SourceKind.RELEASE,
        source_class=SourceClass.A,
        access=AccessMode.OPEN,
        endpoint="https://www.federalreserve.gov/feeds",
        latency_class="event",
        jurisdiction="US",
        terms="Public domain.",
    ),
    SourceSpec(
        key="ecb_press",
        name="ECB press releases",
        publisher="European Central Bank",
        kind=SourceKind.RELEASE,
        source_class=SourceClass.A,
        access=AccessMode.OPEN,
        endpoint="https://www.ecb.europa.eu/rss",
        latency_class="event",
        jurisdiction="EU",
        terms="Reuse permitted with attribution.",
    ),
    SourceSpec(
        key="sec_edgar",
        name="SEC EDGAR filings",
        publisher="US Securities and Exchange Commission",
        kind=SourceKind.RELEASE,
        source_class=SourceClass.A,
        access=AccessMode.OPEN,
        endpoint="https://data.sec.gov",
        latency_class="event",
        jurisdiction="US",
        terms="Public domain; a declared User-Agent and a request rate limit are required.",
        notes="Primary source for anything about a held company.",
    ),
)

NEWS: tuple[SourceSpec, ...] = (
    SourceSpec(
        key="guardian_open",
        name="Guardian Open Platform",
        publisher="Guardian News & Media",
        kind=SourceKind.NEWS,
        source_class=SourceClass.B,
        access=AccessMode.FREE_KEY,
        endpoint="https://content.guardianapis.com",
        latency_class="realtime",
        terms="Free developer tier; content may not be redistributed.",
        notes="One of the few quality outlets with a genuinely open, documented API.",
    ),
    SourceSpec(
        key="gdelt",
        name="GDELT global coverage",
        publisher="The GDELT Project",
        kind=SourceKind.SIGNAL,
        source_class=SourceClass.C,
        access=AccessMode.OPEN,
        endpoint="https://api.gdeltproject.org/api/v2",
        latency_class="realtime",
        terms="Open for research and personal use.",
        notes=(
            "Answers 'is this story spreading, and where' — a coverage measurement, not a "
            "claim about the world. Never a state input."
        ),
    ),
)


CATALOGUE: tuple[SourceSpec, ...] = (*MACRO_SERIES, *OFFICIAL_RELEASES, *NEWS)


class SourceRegistry:
    """The catalogue, queryable. Immutable and offline."""

    __slots__ = ("_by_key", "_specs")

    def __init__(self, specs: Iterable[SourceSpec] = CATALOGUE) -> None:
        by_key: dict[str, SourceSpec] = {}
        for spec in specs:
            if spec.key in by_key:
                raise ValueError(f"duplicate source key {spec.key!r}")
            by_key[spec.key] = spec
        self._by_key = by_key
        self._specs = tuple(sorted(by_key.values(), key=lambda spec: spec.key))

    def __iter__(self) -> Iterator[SourceSpec]:
        return iter(self._specs)

    def __len__(self) -> int:
        return len(self._specs)

    def __getitem__(self, key: str) -> SourceSpec:
        return self._by_key[key]

    def of_kind(self, *kinds: SourceKind) -> tuple[SourceSpec, ...]:
        return tuple(spec for spec in self._specs if spec.kind in kinds)

    def state_inputs(self) -> tuple[SourceSpec, ...]:
        """Every source permitted to move a world-state dimension."""
        return tuple(spec for spec in self._specs if spec.may_move_state)

    def attention_only(self) -> tuple[SourceSpec, ...]:
        """Every source that may raise a question but never change a number."""
        return tuple(spec for spec in self._specs if not spec.may_move_state)

    def requiring_credentials(self) -> tuple[SourceSpec, ...]:
        return tuple(spec for spec in self._specs if spec.needs_credential)

    def ready_for_adapters(self) -> tuple[SourceSpec, ...]:
        """Entries checked against the live service. An adapter may ship only for these."""
        return tuple(
            spec for spec in self._specs if spec.verification is VerificationStatus.CONFIRMED
        )


REGISTRY = SourceRegistry()
