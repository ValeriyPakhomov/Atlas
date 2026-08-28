"""Guards for A02 (time is explicit) and A07 (replay and live share one engine)."""

from __future__ import annotations

import ast
import re
from datetime import UTC, datetime
from pathlib import Path

import pytest

from atlas.domain.clock import Clock, FixedClock, SystemClock
from tests.conftest import PACKAGES_ROOT, REPO_ROOT

WALL_CLOCK_CALLS = re.compile(
    r"\b(datetime\.now|datetime\.utcnow|date\.today|time\.time|time\.monotonic)\b"
)
CLOCK_MODULE = PACKAGES_ROOT / "domain" / "clock.py"


def _library_sources() -> list[Path]:
    return sorted(
        p for p in PACKAGES_ROOT.rglob("*.py") if "__pycache__" not in p.parts and p != CLOCK_MODULE
    )


@pytest.mark.parametrize("path", _library_sources(), ids=lambda p: str(p.name))
def test_library_code_reads_time_only_through_the_clock_port(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    # Strip docstrings so prose about time does not trip the scan.
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            source = source.replace(node.value, "")
    hits = sorted(set(WALL_CLOCK_CALLS.findall(source)))
    assert not hits, (
        f"{path.relative_to(REPO_ROOT)} calls {hits} directly; inject a Clock so the "
        "same code path serves both a live cycle and a historical replay (A07)"
    )


def test_system_clock_is_timezone_aware() -> None:
    now = SystemClock().now()
    assert now.tzinfo is not None
    assert isinstance(SystemClock(), Clock)


def test_fixed_clock_is_deterministic() -> None:
    instant = datetime(2026, 8, 28, 10, 0, tzinfo=UTC)
    clock = FixedClock(instant)
    assert clock.now() == instant == clock.now()
    assert isinstance(clock, Clock)


def test_fixed_clock_rejects_naive_instants() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        FixedClock(datetime(2026, 8, 28, 10, 0))
