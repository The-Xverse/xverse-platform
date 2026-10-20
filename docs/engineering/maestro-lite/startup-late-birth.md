# Late startup return and unknown-birth result composition

Status: selected owned verification on unchanged production code; full17 open.
[Original startup ownership](startup-ownership.md) and RUNTIME-0002/0008 govern.

Four low-level controls exercise an actual child with delayed Popen return, a
cancelled pending return, constructor exception after actual birth, and product
pidfd-open failure. The test bootstrap retains its own original Popen/pidfd before
injecting a delay/error; that external capability is never supplied to the product.
Late/cancelled returns acquire original product cleanup and are reaped/disposed.
Missing original capabilities remain unknown without retry, discovery or adoption,
even after the external bootstrap reaps the actual child. Changed/matching repeats
cannot create another process. Active spawn locks reject conflicting drain/disposal;
cancellation closes the original latch independently before return.

Two whole-runtime controls verify the same missing-capability paths through start.
The caller receives its original in-memory incomplete result with no dispatch or
closure and unknown supervisor cleanup. Matching start returns that result and
collect returns no collection. External actual cleanup cannot upgrade the result
or enable product disposal. Descriptor cleanup is explicitly harness-owned where
the product lacks a provable wait; no result metadata is repaired to manufacture it.

Original low-level61015 terminal0 passes4 per source/wheel phase; whole-entry70802
terminal0 passes2 per phase. Audits retain12 absent owned reservations,4 product
original waits and8 external original waits, preserving all8 unknown product
outcomes after external cleanup. Production81 files are byte-identical to the
prior69-check startup-ownership scope; these6 additional checks describe selected
75 per phase across exact snapshots, not a complete regression. No source defect
was found or repaired; CAPA25 records/133 bindings and historical uncertainties
remain unchanged.135/222/286/287 are not resolved by these controls.

See [low-level evidence](evidence/affa17/startup-late-birth-20261019a/verification.json),
[whole-entry evidence](evidence/affa17/startup-late-birth-20261019b/verification.json),
[partial trace](evidence/affa17/startup-late-birth-partial-traceability.json) and
[continuation](evidence/affa17/continuation-startup-late-birth-20261019.md).
Initial Popen/kernel stalls are not claimed bounded by these injected-return tests;
external facility admission remains necessary. Full late-spawn/startup/crash and
runtime matrices,18 source-parent semantics,24 requirements,30 pairs/90 endpoints,
nine full cases,seven P3 tasks,M1/regression/independent full review and stable17
remain open. Actual admitted service/M1 runs0. No acceptance/merge, factory run,
scientific result or automatic CAPA/025 integration follows.
