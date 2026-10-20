# Preserve terminal results when optional RPC diagnostics are unavailable

Status: partial candidate repair, selected source/wheel verified; full17 unfinished.
[ADR-RUNTIME-0007](ADR-ML3-RUNTIME-0007.md) records the failure contract before code.

The original runtime could finish actual root/helper cleanup and then discard its
result when optional RPC diagnostic ownership checks raised. It also returned
replaced or reflectively altered diagnostic data without validation. Three owned
post-cleanup fault controls reproduced these outcomes in both source and wheel.
Original metadata was restored only after factual cleanup for local disposal;
no result, ACK, ownership or normal evidence was manufactured.

PersistenceClient now pins the first frozen failure reference and its original
field values. Its getter validates owner/reference/type/content and reports an
explicit context error when metadata is unavailable. The runtime contains that
optional read: RuntimeResult retains the actual incomplete execution/cleanup facts,
sets persistence_failure=None and adds ML-RUNTIME-RPC-CONTEXT-UNRESOLVED. Matching
replay retains the original result rather than upgrading its unknown observations.
Diagnostic capture/attachment itself is best effort and cannot bypass original
RPC failure cancellation, rethrow or lock release. No deadline, permit, native
protocol, normal record or accepted top-level export changes.

Original context-loss-a91682 terminal1 has3 failed checks per phase; the remaining
28 selected checks per phase were skipped. b97486 terminal0 passes60 per phase.
A separate source review then identified the missing-pin capture concern; c78394
terminal0 passes61 per phase including the new active blocked-worker control.
No unchanged retry or old timeout extension occurred. c's audit verifies122 absent
owned reservations,6 post-cleanup fault observations,2 active missing-pin controls
without external fallback,10 earlier actual failure contexts,12 primary startup
cleanup results,254 M3 links in retained runtime projections and4 closed original-
input recomputations. Old client wait-ownership negatives remain explicit unknowns.
These are owned components, not actual admitted RuntimeService/M1 execution.

[CAPA300](evidence/affa17/capa-20261019-rpc-context-loss/register.json) retains the
original failures, exact correction and additional source-concern patch.23 records/
117 evidence bindings validate; all effectiveness NOT_DEMONSTRATED.135/222/286/287
remain UNRESOLVED/UNKNOWN. Same-session controls do not establish independent causal
confirmation, an effectiveness observation window or stable17.

See [partial trace](evidence/affa17/rpc-context-loss-partial-traceability.json),
[red audit](evidence/affa17/rpc-context-loss-20261019a/verification.json),
[current audit](evidence/affa17/rpc-context-loss-20261019c/verification.json) and
[continuation](evidence/affa17/continuation-rpc-context-loss-20261019.md).
Future optional diagnostics must remain subordinate to original cleanup/results;
unavailable observations stay unknown and never authorize execution. Full024
source-parent/requirement/runtime matrices,M1,regression,independent complete review,
stable17,acceptance and delivery remain open. CAPA is manual observation-only;
capability025 has no automated CAPA integration or gate effect.
