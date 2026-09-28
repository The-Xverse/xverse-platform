"""Run negative controls before the 26 trusted Phase 6 conformance inspections."""

import sys
import unittest

import test_phase6_conformance
from check_phase6_conformance import main


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_phase6_conformance)
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=1).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    main()
