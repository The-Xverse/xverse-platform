# Original supervisor startup ownership after alias loss

Status: partial candidate repair, selected source/wheel verified; full17 open.
[ADR-RUNTIME-0008](ADR-ML3-RUNTIME-0008.md) precedes source repair.

The pending launcher previously accepted substituted process/channel/session/pidfd/
capability aliases. A different genuine capability could select an unrelated child
for cancellation; a substituted Popen received the original child's returncode.
A lost session alias could interrupt actual cleanup/outcome inspection. Controlled
owned tests reproduce these failures; a foreign-signal guard denies every sentinel
signal attempt, so this is not evidence of an external target incident.

The launcher now pins each actual resource immediately when returned. Ordinary
launch/registration/repeat validation rejects changed aliases or process PID.
Creation and registration use retained local resources. Independent cleanup-only
holder/cancel/drain/outcome/disposal use original resource pins and the original
captured cleanup end/session. After READY, the original native session keeps root
wait ownership; failed registration uses the original launcher private pidfd.
A missing original birth/capability stays unknown without PID/path discovery,
adoption, second creation or fabricated wait. Existing admission, start windows,
native fencing and drain bounds remain. Accepted top-level APIs are unchanged.

Original a13475 fails5 controls per phase before injection because its Popen function
wrapper violates exact-class child validation. Early assertion also skips sentinel
wait cleanup; those original waits remain unacknowledged, never retrospectively
claimed. Corrected observational-subclass harness b96798 reaches5 real faults per
phase on identical81 production files: all fail. It records4 guard-denied signal
attempts across phases, foreign returncode mutation and4 external root cleanups.
All sentinels remain kernel-alive during product control; b's final waits are in
unconditional harness code without separate wait receipts.

Current c25844 passes69 source/wheel checks per phase. Audit verifies122 absent
owned reservations,10 reached alias controls withzero foreign signal attempts,
correct original supervisor waits without external root fallback,10 explicit
harness sentinel wait receipts,12 primary startup cleanup results,508 actual M3
links in runtime projections and8 closed original-input recomputations. The fault
harness still disposes its original descriptors separately after factual waits;
this does not establish the entire disposal/late-birth matrix. Native wait-ownership
negatives preserve uncertainty. Only launcher production code changes among81 files.

See [partial trace](evidence/affa17/startup-ownership-partial-traceability.json),
[red ownership audit](evidence/affa17/startup-ownership-20261019b/verification-v2.json),
[current audit](evidence/affa17/startup-ownership-20261019c/verification-v2.json),
[CAPA](evidence/affa17/capa-20261019-startup-ownership/register.json) and
[continuation](evidence/affa17/continuation-startup-ownership-20261019.md).
CAPA307/308 are local fix candidates, not independently confirmed causes or
effectiveness closure.25 records/133 bindings validate; all effectiveness remains
NOT_DEMONSTRATED and135/222/286/287 remain unresolved. Full24 requirements,18 source
semantics,30 pairs/90 endpoints,nine runtime cases,seven tasks,M1/regression/full
independent review/stable17 and acceptance remain open. No actual admitted service
execution, factory run, scientific result or automatic025 CAPA integration.
