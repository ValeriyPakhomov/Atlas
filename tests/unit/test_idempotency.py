"""Queue 02 — stage 0: deterministic identity and deduplication (ADR-0007)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from atlas.ingestion.contracts import AdapterDescriptor, FetchedItem
from atlas.ingestion.idempotency import (
    DedupeLayer,
    Deduplicator,
    InMemoryLedger,
    ItemIdentity,
    canonical_url,
    content_hash,
    identify,
    normalise_text,
)
from atlas.scoring.relevance import SourceClass

NOW = datetime(2026, 8, 29, 9, 0, tzinfo=UTC)

REUTERS = AdapterDescriptor(name="reuters", source_type="wire", source_class=SourceClass.A)
AGGREGATOR = AdapterDescriptor(name="aggregator", source_type="rss", source_class=SourceClass.C)


def item(**overrides: Any) -> FetchedItem:
    fields: dict[str, Any] = {"observed_at": NOW, "title": "Central bank holds rates"}
    fields.update(overrides)
    return FetchedItem(**fields)


# ── canonical URLs ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://Example.com/Story", "https://example.com/Story"),
        ("https://www.example.com/story/", "https://example.com/story"),
        ("https://example.com:443/story", "https://example.com/story"),
        ("http://example.com:80/story", "http://example.com/story"),
        ("https://example.com/story#section", "https://example.com/story"),
        ("https://example.com/story?utm_source=news&id=7", "https://example.com/story?id=7"),
        ("https://example.com/story?b=2&a=1", "https://example.com/story?a=1&b=2"),
        ("https://example.com//a//b", "https://example.com/a/b"),
        ("example.com/story", "https://example.com/story"),
        ("  https://example.com/story  ", "https://example.com/story"),
    ],
)
def test_canonical_url_folds_only_what_cannot_change_the_document(raw, expected):
    assert canonical_url(raw) == expected


@pytest.mark.parametrize(
    "raw", [None, "", "   ", "mailto:someone@example.com", "ftp://example.com/x", "just a note"]
)
def test_canonical_url_refuses_to_invent_an_address(raw):
    assert canonical_url(raw) is None


def test_case_in_the_path_is_preserved():
    """Hosts are case-insensitive; paths are not. Folding them would merge real pages."""
    assert canonical_url("https://example.com/A") != canonical_url("https://example.com/a")


def test_pagination_and_amp_are_left_alone():
    """A merge that is only usually right silently deletes items. We do not guess."""
    assert canonical_url("https://example.com/a/amp") == "https://example.com/a/amp"
    assert canonical_url("https://example.com/a?page=2") == "https://example.com/a?page=2"


# ── content hashing ─────────────────────────────────────────────────────────


def test_normalisation_folds_presentation_not_content():
    typeset = "  The  ECB\u2019s   \u201cdecision\u201d\u00a0"
    assert normalise_text(typeset) == normalise_text('the ecb\'s "decision"')
    assert normalise_text("Rate cut") != normalise_text("Rate rise")


def test_content_hash_is_stable_and_versioned():
    first = content_hash("Title", "Body")
    assert first is not None
    assert first.startswith("sha256-v1:")
    assert first == content_hash("Title", "Body")
    assert first != content_hash("Body", "Title")


def test_empty_content_has_no_content_identity():
    """Hashing emptiness would collapse every text-free item into a single one."""
    assert content_hash(None, None) is None
    assert content_hash("", "   ") is None


# ── identity ────────────────────────────────────────────────────────────────


def test_identity_carries_the_versions_that_produced_it():
    identity = identify(item(external_id="7", url="https://example.com/a"), REUTERS)
    assert identity.external_key == "ext:reuters:7"
    assert identity.url_key == "url:https://example.com/a"
    assert identity.content_key is not None
    assert identity.canonicalisation_version == "url-canon-v1"
    assert identity.normalisation_version == "text-norm-v1"
    assert identity.parse_version == "1"
    assert [layer for layer, _ in identity.layers()] == list(DedupeLayer)


def test_identity_without_any_layer_is_refused():
    with pytest.raises(ValueError, match="has no identity"):
        ItemIdentity(
            source_name="x",
            external_key=None,
            url_key=None,
            content_key=None,
            parse_version="1",
        )


def test_storage_hash_never_pretends_to_hash_absent_content():
    identity = identify(item(external_id="7", title=None, body=None), REUTERS)
    assert identity.content_key is None
    assert identity.storage_hash.startswith("ident-v1:")


# ── deduplication ───────────────────────────────────────────────────────────


def dedupe() -> Deduplicator:
    return Deduplicator(InMemoryLedger())


def test_the_same_item_twice_is_recognised_by_its_external_id():
    d = dedupe()
    identity = identify(item(external_id="7"), REUTERS)

    assert d.register(identity, "ref-1").is_new is True
    second = d.register(identity, "ref-2")
    assert second.is_new is False
    assert second.layer is DedupeLayer.EXTERNAL_ID
    assert second.matched_ref == "ref-1"


def test_external_ids_do_not_collide_across_sources():
    """Provider ids are only meaningful inside the provider's namespace."""
    d = dedupe()
    d.register(identify(item(external_id="1", title="Wire story"), REUTERS), "ref-1")
    verdict = d.register(identify(item(external_id="1", title="Unrelated blog"), AGGREGATOR), "b")
    assert verdict.is_new is True


def test_the_same_url_reached_through_two_sources_is_one_artifact():
    d = dedupe()
    url = "https://example.com/story"
    d.register(identify(item(external_id="7", url=url), REUTERS), "ref-1")

    verdict = d.register(
        identify(item(external_id="99", url=f"{url}?utm_source=newsletter"), AGGREGATOR),
        "ref-2",
    )
    assert verdict.is_new is False
    assert verdict.layer is DedupeLayer.CANONICAL_URL
    assert "same URL" in verdict.explanation


def test_syndicated_wire_copy_is_one_artifact_not_six_corroborations():
    """The identical text run by another outlet is not independent confirmation."""
    d = dedupe()
    body = "The central bank left its policy rate unchanged at 4.25 percent."
    d.register(identify(item(external_id="a", body=body), REUTERS), "ref-1")

    verdict = d.register(identify(item(external_id="b", body=body), AGGREGATOR), "ref-2")
    assert verdict.is_new is False
    assert verdict.layer is DedupeLayer.CONTENT_HASH
    assert "identical text" in verdict.explanation


def test_two_different_reports_of_the_same_event_both_survive():
    """Corroboration means two different artifacts, and must not be deduplicated away."""
    d = dedupe()
    assert d.register(
        identify(item(external_id="a", body="Reuters reporting on the decision."), REUTERS),
        "ref-1",
    ).is_new
    other = item(external_id="b", body="A different account of the same meeting.")
    assert d.register(identify(other, AGGREGATOR), "ref-2").is_new


def test_classify_does_not_record():
    d = dedupe()
    identity = identify(item(external_id="7"), REUTERS)
    assert d.classify(identity).is_new is True
    assert d.classify(identity).is_new is True


def test_the_first_reference_wins_forever():
    ledger = InMemoryLedger()
    d = Deduplicator(ledger)
    identity = identify(item(external_id="7"), REUTERS)
    d.admit(identity, "ref-1")
    d.admit(identity, "ref-2")
    assert ledger.lookup("ext:reuters:7") == "ref-1"
