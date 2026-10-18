# Separate read-only regression review before successor repair

18 October 2026, ML3-LAUNCHER9 v2. Same-agent component review, not an independent
full-candidate review or acceptance. Preserve the complete rejected v2 source and
regression bundle before repairs; exact source hashes are in its source manifest.

8. MAJOR verification: the inherited full-platform runner unsets PYTHONPATH and
   therefore uses the installed candidate. Run the full platform suite explicitly
   against src while keeping the copied wheel consumer isolated. Account for the
   existing nested Argus regression run: fork receipts must match actual complete
   process groups, rather than requiring one receipt for the whole full-platform
   invocation. Do not weaken any original root/helper audit.
9. MINOR integration test: the installed regression passed 410 cases but failed
   the storage-after-Arm cleanup assertion. Native cancellation may kill/reap while
   C1 samples membership; C1 correctly retains ML-TEARDOWN-MEMBERSHIP-UNKNOWN.
   Confirm native direct-child drain first, then separately verify original C1
   cleanup. Use that order in positive cleanup and fixture teardown too. Require
   actual empty/released C1 for every surviving fixture boundary; do not label an
   unresolved observation as success. This is component cleanup coordination, not
   implemented general lifecycle teardown or a hard kernel bound.

No product failure, safety claim, full M1 closure or accepted-main change is inferred
from these findings. Repeat full source and installed regressions for the successor.
