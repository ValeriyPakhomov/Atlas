"""Atlas scoring — the dashboard score and news relevance.

Deterministic by construction: no model produces a score, and every point decomposes
into a stored contribution row (`docs/product/ATLAS_SCORE.md`).
"""

from atlas.scoring.domain_score import (
    Contribution,
    ContributionKind,
    DimensionExposure,
    DomainScore,
    DomainScoreInputs,
    ImpactContribution,
    PolicyOutcome,
    ScoreWeights,
    overall_score,
    score_domain,
)
from atlas.scoring.relevance import (
    RELEVANCE_FLOOR,
    RelevanceInputs,
    RelevanceVerdict,
    SourceClass,
    score_relevance,
)

__all__ = [
    "RELEVANCE_FLOOR",
    "Contribution",
    "ContributionKind",
    "DimensionExposure",
    "DomainScore",
    "DomainScoreInputs",
    "ImpactContribution",
    "PolicyOutcome",
    "RelevanceInputs",
    "RelevanceVerdict",
    "ScoreWeights",
    "SourceClass",
    "overall_score",
    "score_domain",
    "score_relevance",
]
