"""Worker entrypoint.

Queue 00 ships the process boundary only. ``run_atlas_cycle`` (blueprint §19) is
assembled in Queue 13 and will be invoked from here behind a scheduler.
"""

from __future__ import annotations

import sys

from atlas.config import get_settings
from atlas.domain.clock import SystemClock


def main(argv: list[str] | None = None) -> int:
    """Report worker readiness. No jobs are registered yet."""
    _ = argv if argv is not None else sys.argv[1:]
    settings = get_settings()
    clock = SystemClock()
    print(
        f"atlas-worker ready environment={settings.environment} "
        f"as_of={clock.now().isoformat()} scheduled_jobs=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
