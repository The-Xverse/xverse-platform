"""Per-module receipt namespace for every pytest session in the verification harness (v2).

Successor of integrated-maestro-20261019b/receipt_namespace.py. Differences:
- Importable by name (``PYTEST_PLUGINS=maestro_receipt_namespace``) from the prepared
  verification environment, so a child pytest spawned by an accepted test, such as
  test_existing_platform_pytest_regression_unchanged_in_assembled_target, also receives
  one receipt directory per module instead of one shared inherited directory.
- Captures the receipt root once at import; each test then exports a child root
  ``<root>/<module>/nested`` so nested sessions never share the outer directories.
- Tolerates an unset root (does nothing), so unrelated subprocess sessions are unchanged.

Verification harness only. It does not change product, tests, XDL or any assertion.
"""
import os
from pathlib import Path

import pytest

_ROOT = os.environ.get("MAESTRO_FULL_RECEIPT_ROOT")


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    if not _ROOT:
        return
    target = Path(_ROOT) / item.path.stem
    target.mkdir(parents=True, exist_ok=True)
    os.environ["MAESTRO_BOUNDARY_RECEIPTS"] = str(target)
    os.environ["MAESTRO_FULL_RECEIPT_ROOT"] = str(target / "nested")
