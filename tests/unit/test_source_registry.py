"""The source catalogue, and the one rule it enforces as a type invariant."""

from __future__ import annotations

import pytest

from atlas.domain.sensitivity import SensitivityTier
from atlas.ingestion.registry import (
    CATALOGUE,
    REGISTRY,
    AccessMode,
    SourceKind,
    SourceRegistry,
    SourceSpec,
    VerificationStatus,
)
from atlas.scoring.relevance import SourceClass


def spec(**overrides: object) -> SourceSpec:
    fields: dict[str, object] = {
        "key": "example",
        "name": "Example",
        "publisher": "Example Publisher",
        "kind": SourceKind.SERIES,
        "source_class": SourceClass.A,
        "access": AccessMode.OPEN,
        "endpoint": "https://example.com/api",
        "latency_class": "daily",
        "terms": "Open data.",
    }
    fields.update(overrides)
    return SourceSpec(**fields)  # type: ignore[arg-type]


# ── series move state, news moves attention ─────────────────────────────────


def test_a_measured_series_may_move_state():
    assert spec(kind=SourceKind.SERIES).may_move_state is True
    assert spec(kind=SourceKind.RELEASE).may_move_state is True
    assert spec(kind=SourceKind.MARKET).may_move_state is True


def test_reporting_never_moves_state_however_reliable_the_outlet():
    """Otherwise 'the state of the economy' becomes the mood of the press about it."""
    assert spec(kind=SourceKind.NEWS, source_class=SourceClass.A).may_move_state is False
    assert spec(kind=SourceKind.NEWS, source_class=SourceClass.B).may_move_state is False


def test_a_weak_class_cannot_move_state_even_when_it_publishes_numbers():
    assert spec(kind=SourceKind.SERIES, source_class=SourceClass.D).may_move_state is False


def test_state_permission_is_derived_and_cannot_be_declared():
    assert "may_move_state" not in {field for field in SourceSpec.__slots__}


def test_a_coverage_signal_cannot_be_declared_reliable():
    with pytest.raises(ValueError, match="coverage signal"):
        spec(kind=SourceKind.SIGNAL, source_class=SourceClass.A)


# ── catalogue hygiene ───────────────────────────────────────────────────────


def test_every_entry_is_transport_secure_and_publicly_classified():
    for source in REGISTRY:
        assert source.endpoint.startswith("https://"), source.key
        assert source.default_tier is SensitivityTier.L0, source.key
        assert source.terms.strip(), source.key


def test_a_world_source_cannot_be_classified_as_owner_data():
    with pytest.raises(ValueError, match="L0/L1"):
        spec(default_tier=SensitivityTier.L3)


def test_duplicate_keys_are_refused():
    with pytest.raises(ValueError, match="duplicate source key"):
        SourceRegistry((spec(), spec()))


def test_the_catalogue_stays_small_enough_to_explain():
    """Six feeds Atlas can explain beat sixty it cannot. This is a design limit."""
    assert len(CATALOGUE) <= 20


def test_the_backbone_is_official_open_data():
    state_inputs = REGISTRY.state_inputs()
    assert len(state_inputs) >= 8
    assert all(source.source_class is SourceClass.A for source in state_inputs)
    assert {"fred", "ecb_data", "eurostat", "sec_edgar"} <= {s.key for s in state_inputs}


def test_news_and_coverage_are_attention_only():
    assert {source.key for source in REGISTRY.attention_only()} == {"guardian_open", "gdelt"}


def test_credentials_are_declared_not_discovered():
    assert {source.key for source in REGISTRY.requiring_credentials()} == {
        "fred",
        "eia",
        "guardian_open",
    }
    assert all(not source.needs_credential for source in REGISTRY.of_kind(SourceKind.RELEASE))


def test_no_adapter_may_ship_against_an_unverified_entry():
    """Every entry is unchecked until someone contacts the live service and says so."""
    assert REGISTRY.ready_for_adapters() == ()
    assert all(source.verification is VerificationStatus.NEEDS_CHECK for source in REGISTRY)
