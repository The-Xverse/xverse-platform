# T025 protected integration review

**Review subject:** clean detached candidate `92dde5ff9971867b30c478a3f43b721745dd3edb`
and the separately retained [exact-revision evidence](protected-evidence/README.md).
**Decision:** candidate remains open; final acceptance is not supported yet.

This was a separate read-only review of the frozen integration snapshot after the implementation
and regression passes. No finding in this report has been repaired in that snapshot.

| Finding | Severity | Evidence and required closure |
| --- | --- | --- |
| PI-01: ThreadSanitizer result unavailable | Blocking for the T025 concurrency measure | The TSan build failed when GTest discovery executed the instrumented binary: `FATAL: ThreadSanitizer: unexpected memory mapping`. Run the T025 concurrency cases in a TSan-capable isolated host, retain its exact-revision output, and review it. The ASan/UBSan pass does not substitute for this measure. |
| PI-02: CodeQL result unavailable | Blocking for the protected static/security measure | The protected host has no CodeQL CLI. Obtain an admitted tool and run the agreed C++ query suite on the exact candidate, retaining the database/query/tool identity and results. The worker's clang-tidy result does not substitute for CodeQL. |
| PI-03: repository workflow references remain stale | Acceptance documentation | Capability-007 plan, tasks, acceptance checklist, and the committed `AGENTS.md` still describe SESN as a forward-looking gate. The user's 2026-09-26 direction and the dirty checkout's ADR-0020 supersede that method. Bring the governing decision and affected forward-looking references into the accepted repository revision without changing historical evidence. |

Verified in this pass: the full Fabro run package contains all 833 indexed files with matching
SHA-256 and the four terminal-review files match the source copies; the standalone R6/R5 terminal
review is preserved; the three GTest archives and extracted test prefix were admitted; T025 passed
144/144 ordinary and 144/144 ASan/UBSan tests; the official observation `--all` gate and its three
predecessor gates passed on the exact candidate. The protected FR allocation is recorded in
[integration-traceability.md](integration-traceability.md), with deferred stimulation behavior left
for later tasks. The dirty official checkout was not modified.

The Fabro review and this protected review make different claims. Neither accepts T025 on the user's
behalf. A repair of any finding requires a successor snapshot and affected checks before another
read-only review and explicit user acceptance.
