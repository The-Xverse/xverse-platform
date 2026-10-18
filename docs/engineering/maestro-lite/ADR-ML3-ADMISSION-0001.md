# ADR-ML3-ADMISSION-0001 — exact permits and durable atomic intent claims

Date: 2026-10-18. Status: implementation-candidate decision, not accepted architecture or execution admission.
Scope: U2 and ML-SR-005/006/023/024 of the existing thesis Phase 3 specification.
Parent: ML3-PREP1-2026-10-18-v1; baseline platform `c2997c0f810d117cf45b2e34a4011b3ba7219494`.

## Problem and decision

Accepted M3 `ExecutionPermit.validate` checks temporal and plan/environment/catalog identity
and permits supersets of the plan's actions and operation classes. Maestro additionally
requires exact sets, explicit source approvals, exclusions, duplicate-ID/nonce rejection,
and revalidation immediately before durable consumption. Separate public `permit_consumed`
and `append` calls cannot atomically arbitrate two cooperating admission processes.

Preserve M3 permit types and accepted APIs. Add `claim_intent(record)` to the two concrete
M3 journals, under their existing thread/process locks, as an additive public operation.
Only a pending intent with nonempty execution/action/permit/nonce bindings can be claimed.
The file implementation checks durable history and fsyncs the intent and directory before
returning. A competing claim of the same ID or nonce rejects. A write/fsync uncertainty
does not authorize launch; surviving intent bytes continue to prohibit replay. Unreadable
or unverifiable consumption history rejects instead of being treated as unused. Ordinary
append and existing M3 controller behavior remain unchanged; this additive primitive does
not retroactively prove concurrency guarantees for legacy check-then-append clients.

Use a Maestro `PermitSession` to recompile the prepared result from its original normalized
XDL and compare the complete prepared value. This defeats dataclass replacement of a plan
or unit while retaining its public digest. The session privately retains exact permit
objects and caller-supplied, approval-owner records binding run/unit/generation, provider,
environment, immutable plan/artifact identities and permit content. Records are explicit
trusted inputs from the future admission owner, not self-authenticating human approval.
No string, field equality or this library's return value establishes operator authority.

Validate every unit before creating a session; then recheck the selected unit's permit,
approval and replay status at each intent claim. Unknown exclusion expressions reject;
recognized exclusions are evaluated against the exact declared operations and provider.
The session supplies no workload callback. Durable intent is a prerequisite for the future
Argus append/flush and AFFA ticket sequence, not a launch ticket or a successful lifecycle.
All public reports omit nonce and approval-owner data.

## Limits and alternatives

Python matches accepted M3/XDL/Argus and coordinates control-plane work; the C++ data plane
is unchanged. A separate permit database would duplicate M3 consumption state and is not
introduced. Private M3 lock access from Maestro is rejected in favor of the public atomic
method. A boolean admission flag and a rehashed caller plan cannot substitute for inputs.

The file-journal operation is durable local I/O, not a host-deadline guarantee. Kernel/fsync
stalls require U3 supervision. No provider, containment helper, bootstrap scope, G4 source
semantics, G5 executable proof, Argus lifecycle closure or actual ML3 runtime is admitted.
Execution readiness remains false. Existing accepted M3 APIs/consumers must pass regression.
All 24 requirements, 18 allocation-only source parents and downstream runtime cases remain.

## Verification contract

Store identity refinement after ADM-REV-05: strict claims seal the journal/lock/parent
device and inode identities in the existing lock file before intent publication, then
verify them at every claim/reopen. Missing or replaced history is unknown consumption,
not a new empty store. Partial or uncertain marker publication blocks; it cannot be
reset by the library. Existing lock-file advisory locking remains compatible with
ordinary M3 users; no nonce database or second journal is introduced. This is identity
and accidental-loss detection under an owned-store trust assumption, not protection
against an actor able to rewrite both the private journal and its lock metadata.

Use actual M3 permits and file journals. Exercise exact and surplus scope, unknown/conflicting
exclusions, future/expired permits and approvals, changed provider/environment/plan/artifact,
duplicate ID/nonce, forged prepared values, recheck after preflight, simultaneous independent
process claims, reopen after an intent without outcome, and fsync/write uncertainty. Verify
no provider or ticket is invoked. Retain commands, process return codes, source pins, wheel
consumer checks and the full owning-platform Python regression. Record review findings
before successor repairs; keep the PREP1 worktree and its receipts unchanged.
