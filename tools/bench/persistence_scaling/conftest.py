"""Bench-only fixtures: the platform's owned trusted-host Maestro fixtures (private component-test harness,
not runtime C1 and not M1), imported from this checkout's test package."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tests.thesis_lite.maestro.test_affa_native import authority_binary  # noqa: E402,F401
from tests.thesis_lite.maestro.test_boundary import environment  # noqa: E402,F401
from tests.thesis_lite.maestro.test_launcher import binaries  # noqa: E402,F401
from tests.thesis_lite.maestro.test_run_bootstrap import run_bootstrap_binary  # noqa: E402,F401
