# ADR ML3-CLOSURE-0001 — Original run resource closure

18 October 2026. Partial implementation candidate; not accepted. Parent 42729bd.
External authoritative capability: thesis specs/024-maestro-lite-lifecycle, design
ML-DESIGN-2026-10-03-v2. ML-SR-010–013, 016, 018–020, 022–024 are partial
consumers. All 24 requirements, 18 unvalidated/null-mapped REF-002 parents,
30 scenario pairs, 90 endpoints and nine full runtime cases remain binding.

Use Python for bounded coordinator composition and storage-worker status decoding;
retain native C original wait/fence/containment mechanisms without wire changes.
Bootstrap records original birth role/helper/unit descriptors before the RPC and
retains exact adapter clients after construction. Failed constructors and late/
unacknowledged births remain in the same inventory; caller-supplied lists never
assert completeness. No PID/path discovery, replacement registry or adoption.

RunClosure uses original bootstrap/optional exact FiniteDispatcher. Close requires
nonblocking original normal-operation locks; independent cancel bypasses them.
Normal unit teardown precedes one bounded storage-worker incomplete-closure attempt,
then graceful original helper drain, original root drain and exact C1 release of
all retained issued boundaries. Each phase preserves a share of the original end;
no retry extends it. Continue after individual failures; retain unknown facts.

Storage closure uses public writer state, successful public flush as positive
usability evidence, at most one abort of an open usable writer, and the accepted
reader's actual durable manifest. Storage failure does not gate C1/helper cleanup.
No private stream inspection, reopen, finalize-as-complete or invented durable state.
The incomplete-closure RPC replaces the existing one-call abort reserve; legacy
abort remains compatible. RPC failure reports unknown current state and separately
the last acknowledged state. Exact ACK decoding precedes client state updates.

Run results separate execution, unit/issued-boundary cleanup, original helper/root
reaps, unknown births, writer state/usability and durable manifest observations.
Native direct-child wait is established only by original Query/teardown or original
native issuer's verified zero exit, never boundary emptiness. Local FDs remain
retained for caller disposal; lifecycle_complete/ready_for_execution remain false.
No full M1/global epoch, initial authenticated bootstrap/environment admission,
recovery/restart, U7/U8 or acceptance claim. No factory run, main merge, legacy or
scientific-protocol change. Sol/high recommended; same-agent separate read-only
review is required, independent full-candidate review remains pending.
