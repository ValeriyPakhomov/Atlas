"""Atlas events — canonical events, deterministic dedupe and rule-based scores (Queue 03).

Reading order: :mod:`~atlas.events.scoring` (the three numbers on every event), then
:mod:`~atlas.events.normalization` (many accounts to one canonical event), then
:mod:`~atlas.events.dedupe` (the deterministic spine and the advisory layer, ADR-0007).

Nothing in this package calls a model or reads the wall clock.
"""

from atlas.events.dedupe import (
    DEFAULT_MERGE_POLICY,
    DecidedBy,
    DecisionLog,
    EventGraph,
    EventMergeProposal,
    EventRecord,
    MergeDecision,
    MergeMethod,
    MergeOutcome,
    MergePolicy,
    MergeResult,
    entity_time_topic_score,
    jaccard,
)
from atlas.events.normalization import (
    ATLAS_EVENT_NAMESPACE,
    EVENT_KEY_VERSION,
    EventCandidate,
    build_event,
    event_dedupe_key,
    normalise_event_type,
    normalise_terms,
)
from atlas.events.scoring import (
    DEFAULT_CLASS_CEILING,
    DEFAULT_SCORING,
    EventScoringPolicy,
    Report,
    credibility,
    distinct_sources,
    novelty,
    urgency,
)

__all__ = [
    "ATLAS_EVENT_NAMESPACE",
    "DEFAULT_CLASS_CEILING",
    "DEFAULT_MERGE_POLICY",
    "DEFAULT_SCORING",
    "EVENT_KEY_VERSION",
    "DecidedBy",
    "DecisionLog",
    "EventCandidate",
    "EventGraph",
    "EventMergeProposal",
    "EventRecord",
    "EventScoringPolicy",
    "MergeDecision",
    "MergeMethod",
    "MergeOutcome",
    "MergePolicy",
    "MergeResult",
    "Report",
    "build_event",
    "credibility",
    "distinct_sources",
    "entity_time_topic_score",
    "event_dedupe_key",
    "jaccard",
    "normalise_event_type",
    "normalise_terms",
    "novelty",
    "urgency",
]
