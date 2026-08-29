"""Concrete source adapters.

Queue 02 ships the two that need no network: the owner's own submissions, and a fixture
adapter that makes replay determinism testable. Market and news providers land with their
own queue items, behind the same contract.
"""

from atlas.ingestion.adapters.fixture import FixtureAdapter
from atlas.ingestion.adapters.manual import ManualSubmissionAdapter, OwnerSubmission

__all__ = ["FixtureAdapter", "ManualSubmissionAdapter", "OwnerSubmission"]
