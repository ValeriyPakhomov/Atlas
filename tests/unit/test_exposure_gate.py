"""Queue 02 — stage 1: the exposure gate."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from atlas.domain.sensitivity import SensitivityTier
from atlas.ingestion.contracts import AdapterDescriptor, FetchedItem
from atlas.ingestion.triage import (
    ExposureGate,
    ExposureKind,
    ExposureProfile,
    ExposureTerm,
    GatePolicy,
    MatchMode,
    TriageStage,
    exposure_score,
)
from atlas.scoring.relevance import DiscardReason, SourceClass

NOW = datetime(2026, 8, 29, 9, 0, tzinfo=UTC)

WIRE = AdapterDescriptor(name="wire", source_type="rss", source_class=SourceClass.B)
OWNER = AdapterDescriptor(
    name="owner",
    source_type="manual",
    source_class=SourceClass.A,
    default_tier=SensitivityTier.L3,
    owner_authored=True,
)

NVDA = ExposureTerm(
    key="instrument:NVDA",
    label="NVDA",
    kind=ExposureKind.INSTRUMENT,
    weight=Decimal("0.9"),
    aliases=("NVDA",),
    match_mode=MatchMode.SYMBOL,
)
NVIDIA = ExposureTerm(
    key="entity:nvidia",
    label="Nvidia",
    kind=ExposureKind.ENTITY,
    weight=Decimal("0.9"),
    aliases=("Nvidia Corporation",),
)
GEORGIA = ExposureTerm(
    key="country:GE",
    label="Georgia",
    kind=ExposureKind.COUNTRY,
    weight=Decimal("0.8"),
    aliases=("Georgian government", "Tbilisi"),
)
COFFEE = ExposureTerm(
    key="sector:coffee",
    label="coffee futures",
    kind=ExposureKind.SECTOR,
    weight=Decimal("0.05"),
)


def profile(*terms: ExposureTerm) -> ExposureProfile:
    return ExposureProfile(terms or (NVIDIA, GEORGIA))


def item(title: str | None = None, body: str | None = None) -> FetchedItem:
    return FetchedItem(observed_at=NOW, external_id="x1", title=title, body=body)


def gate(*terms: ExposureTerm, policy: GatePolicy | None = None) -> ExposureGate:
    return ExposureGate(profile(*terms), policy)


# ── matching ────────────────────────────────────────────────────────────────


def test_a_single_word_term_matches_case_insensitively():
    matches = profile().matches("NVIDIA beats expectations")
    assert [m.term_key for m in matches] == ["entity:nvidia"]
    assert matches[0].matched_text == "NVIDIA"


def test_a_multi_word_alias_matches_as_a_phrase():
    matches = profile().matches("The Georgian government announced new rules")
    assert [m.term_key for m in matches] == ["country:GE"]
    assert matches[0].matched_text == "Georgian government"


def test_a_term_is_reported_once_however_often_it_appears():
    matches = profile().matches("Nvidia said. Nvidia added. Nvidia repeated.")
    assert len(matches) == 1


def test_matches_are_ordered_deterministically():
    text = "Tbilisi and Nvidia in the same sentence"
    first = profile().matches(text)
    assert [m.term_key for m in first] == ["country:GE", "entity:nvidia"]
    assert first == profile().matches(text)


def test_unrelated_text_matches_nothing():
    assert profile().matches("Rainfall records broken in Patagonia") == ()


def test_a_substring_is_not_a_match():
    """``Georgia`` must not fire on ``Georgian`` handled as a token, nor on ``Georgetown``."""
    assert profile().matches("Georgetown University opened applications") == ()


# ── symbols ─────────────────────────────────────────────────────────────────


def test_symbols_are_matched_case_sensitively():
    it_ticker = ExposureTerm(
        key="instrument:IT",
        label="IT",
        kind=ExposureKind.INSTRUMENT,
        weight=Decimal("0.6"),
        match_mode=MatchMode.SYMBOL,
    )
    p = ExposureProfile((it_ticker,))
    assert p.matches("The company said it will hire") == ()
    assert [m.term_key for m in p.matches("Gartner (IT) reported earnings")] == ["instrument:IT"]


def test_symbol_matching_stands_down_in_all_caps_text():
    us_ticker = ExposureTerm(
        key="instrument:US",
        label="US",
        kind=ExposureKind.INSTRUMENT,
        weight=Decimal("0.7"),
        match_mode=MatchMode.SYMBOL,
    )
    p = ExposureProfile((us_ticker,))
    assert p.matches("US FED HOLDS RATES STEADY AGAIN THIS MONTH") == ()
    assert p.matches("Shares of US closed higher") != ()


def test_symbol_terms_must_be_written_as_they_appear():
    with pytest.raises(ValueError, match="symbol phrases"):
        ExposureTerm(
            key="instrument:nvda",
            label="nvda",
            kind=ExposureKind.INSTRUMENT,
            match_mode=MatchMode.SYMBOL,
        )


# ── profile identity ────────────────────────────────────────────────────────


def test_profile_version_is_content_addressed_and_order_independent():
    assert ExposureProfile((NVIDIA, GEORGIA)).version == ExposureProfile((GEORGIA, NVIDIA)).version
    assert ExposureProfile((NVIDIA,)).version != ExposureProfile((NVIDIA, GEORGIA)).version
    assert ExposureProfile((NVIDIA,)).version.startswith("exposure-v1:")


def test_duplicate_terms_are_a_configuration_error():
    with pytest.raises(ValueError, match="duplicate exposure term"):
        ExposureProfile((NVIDIA, NVIDIA))


# ── scoring ─────────────────────────────────────────────────────────────────


def test_exposure_score_is_the_strongest_match_not_the_sum():
    matches = profile(NVIDIA, GEORGIA, COFFEE).matches("Nvidia, Tbilisi and coffee futures")
    assert len(matches) == 3
    assert exposure_score(matches) == Decimal("0.9")


def test_exposure_score_of_nothing_is_zero():
    assert exposure_score(()) == Decimal(0)


# ── the gate ────────────────────────────────────────────────────────────────


def test_an_item_naming_an_exposure_reaches_extraction():
    decision = gate().evaluate(item(title="Nvidia guidance raised"), WIRE, item_ref="ref-1")
    assert decision.admitted is True
    assert decision.reached is TriageStage.EXTRACTION
    assert decision.score == Decimal("0.9")
    assert "Nvidia" in decision.explanation


def test_an_item_naming_nothing_is_dropped_with_a_readable_reason():
    decision = gate().evaluate(
        item(title="Semiconductor export controls tightened"), WIRE, item_ref="ref-2"
    )
    assert decision.admitted is False
    assert decision.stopped_at is TriageStage.EXPOSURE
    assert decision.reason is DiscardReason.NO_EXPOSURE
    assert decision.explanation == "names nothing you are exposed to"
    assert decision.profile_version == profile().version


def test_marginal_exposure_is_dropped_but_names_what_it_matched():
    decision = gate(NVIDIA, COFFEE).evaluate(
        item(title="Coffee futures ease"), WIRE, item_ref="ref-3"
    )
    assert decision.admitted is False
    assert decision.reason is DiscardReason.IMMATERIAL
    assert "Coffee futures" in decision.explanation  # the words as published


def test_the_owner_is_never_gated():
    decision = gate().evaluate(item(body="Look at this, seems important"), OWNER, item_ref="ref-4")
    assert decision.admitted is True
    assert decision.explanation == "you submitted this"


def test_an_empty_profile_admits_rather_than_silently_emptying_the_world():
    decision = ExposureGate(ExposureProfile(())).evaluate(
        item(title="Anything at all"), WIRE, item_ref="ref-5"
    )
    assert decision.admitted is True
    assert "no exposure profile" in decision.explanation


def test_a_source_can_be_declared_always_read():
    policy = GatePolicy(always_admit_sources=frozenset({"wire"}))
    decision = gate(policy=policy).evaluate(item(title="Unrelated"), WIRE, item_ref="ref-6")
    assert decision.admitted is True
    assert "always read" in decision.explanation


def test_the_gate_reads_the_body_and_any_extra_text():
    g = gate()
    assert g.evaluate(item(body="...Nvidia..."), WIRE, item_ref="r").admitted is True
    assert (
        g.evaluate(item(title="Chip earnings"), WIRE, item_ref="r", extra_text=("Nvidia",)).admitted
        is True
    )
