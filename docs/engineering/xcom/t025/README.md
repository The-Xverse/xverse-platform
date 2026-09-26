# T025 candidate transfer and work products

**Status:** protected integration candidate; acceptance and final commit remain pending.
**Fabro run:** `01M3FT90KBYVC04PEQ464VAHAR` against baseline
`d244eeb3aa26f1b27d23d75fabc750380405269f`.

The [complete run package](fabro-run/01M3FT90KBYVC04PEQ464VAHAR) preserves every collected Fabro
output, including requirements and ReqIF export, architecture diagrams and rendered SVGs, design,
unit specifications, source, unit/integration/validation tests and their results, bidirectional trace
links and matrix, inspections and review findings, generated Doxygen/Sphinx documentation, maintenance
guidance, execution logs, checkpoints, delivery artifacts, and the worker capture. It contains 833
files indexed by [`morning-review-index.json`](fabro-run/01M3FT90KBYVC04PEQ464VAHAR/morning-review-index.json)
plus that index itself. The index SHA-256 is
`0824ce77b9ac9cf0bc967d38431bd8e0028a5d81d49fb98b57acff83e55d05e3`.
All 833 copied files were checked against the index after transfer. The separate
[terminal review](terminal-review/01M3FT90KBYVC04PEQ464VAHAR) preserves its Markdown/JSON decision
and fresh test and collector logs. Historical run contents are immutable evidence; host integration
findings are recorded outside the run package.

The protected integration maps the worker's validation-session header and implementation into
`src/xverse/xcom/`, maps its three test suites into `tests/xcom/validation_session/`, and registers
them in the official CMake graph. The authoritative [FR disposition](integration-traceability.md)
corrects the worker's explicitly unverified predecessor-anchor allocation. The
[test dependency record](test-dependency-admission.md) pins GTest in a separate admitted prefix.

T025 delivers bounded time-authority, permit, and session primitives only. Stimulation routing,
journaling, service emulation, production readiness, and T026 onward remain outside this candidate.
Protected exact-revision verification, separate read-only review, and explicit user acceptance remain
required before T025 can be marked complete or this candidate committed as accepted integration.
The [successor evidence](protected-evidence/successor-evidence.md) and separate
[successor integration review](protected-review-successor.md) record the completed checks and
their scope. The [first protected review](protected-review.md) retains the earlier open findings
and their diagnostic history.
