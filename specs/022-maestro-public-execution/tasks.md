# Implementation tasks

Existing platform/Studio task IDs remain unchanged; these IDs belong only to capability022.

- [x] MPX-T01: specification, contract, baseline and initial consistency review. Depends on: none.
- [x] MPX-T02: bounded public submission and effective-input inspection. Depends on: MPX-T01.
- [x] MPX-T03: host/provider bindings, permissions and executable-source isolation. Depends on: MPX-T02.
- [x] MPX-T04: actual lifecycle scheduling, readiness, idempotency and stop. Depends on: MPX-T03.
- [x] MPX-T05: actual Argus lifecycle evidence and source identity bindings. Depends on: MPX-T04.
- [x] MPX-T06: native X-COM provider/observation integration and gap semantics. Depends on: MPX-T05.
- [ ] MPX-T07: Studio three-view shared-run live demonstration. Depends on: MPX-T10.
- [x] MPX-T08: failure/security/compatibility verification and exact-candidate package. Depends on: MPX-T06.
- [x] MPX-T09: separate review, repairs and affected repeated verification. Depends on: MPX-T08.
- [x] MPX-T10: explicit user acceptance, exact main integration and assembled verification. Depends on: MPX-T09.


2026-10-29 runtime checkpoint: MPX-T02–T05 remain in_progress. The public
prototype passes167checks (59new +108baseline) on the exact recorded source;
real edited inputs, two actual child bindings, original Argus receipts, ownership
loss, runtime/root/install grants, cancellation and failure cleanup are verified.
Two existing native C++ baseline tests pass separately; they are not a correlated
Maestro/native-X-COM run. Native integration, Autoverse, Studio views, final review,
user acceptance and main integration remain open. Evidence:
docs/engineering/maestro-public/evidence/runtime/verification.json.

Subsequent implementation review: T02–T05 are now completed for the specified
bounded Linux host-provider prototype using exact candidatec58c889bf and the above
167checks/self-review. This does not admit native/Autoverse providers or accept
the platform. T06 is in_progress; platform-first sequencing correction in
ADR-MPX-0001 moves T07 after T10 while preserving the full required Studio goal.


2026-10-29 accepted platform checkpoint: T06/T08/T09 completed with190passing
checks and3CTest checks, final retained actual-data evidence and separate self-review.
The user explicitly accepted the frozen source; T10 main integration/assembled
verification is in_progress. T07 actual Studio/Autoverse remains pending after T10.
Decision: acceptance-decision.json. Evidence: docs/engineering/maestro-public/evidence/native/verification.json.


T10 complete: user-accepted exact platform boundary is on local main at
f0e57c844bf9a23b18836c86ca6ca11b4f4b1282. Isolated rebuilt/installed verification passes190checks
and3CTest, with the same9SDKmodules, source/test fingerprint and native artifact.
All5 unrelated original local entries remain unchanged. This records integration,
not publication. T07 actual Studio/Autoverse remains open; the full goal is active.
Evidence: docs/engineering/maestro-public/evidence/main/verification.json.
