"""Queue 00 acceptance: the worker process starts and reports readiness."""

from __future__ import annotations

import pytest

from atlas_worker.main import main


def test_worker_entrypoint_returns_success(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "atlas-worker ready" in capsys.readouterr().out
