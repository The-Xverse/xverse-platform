# Owner integration unit contract

ML3-OWNER7-2026-10-18-v1. Partial integration candidate, no run readiness.

- PermitSession(..., initial_generation=0) preserves default behavior; explicit 1
  admits the first execution generation only. revalidate_start_intent requires its
  actual original receipt, current aware UTC, unchanged journal/plan/permit scope.
  public_start_intent reads the actual journal public projection of that receipt;
  sourceRefs hashes its full canonical redacted bytes, never an ad hoc subset.
- GateConnection retains an original actual Popen and private AF_UNIX SOCK_SEQPACKET
  socket with SO_PASSCRED enabled before READY. Match sender PID/UID/GID, original
  pidfd, exact scope, creation epoch and lease; reject copies/forks, FD transfer,
  malformed/foreign/late responses and input substitution. No helper is created.
- ReleaseOwner.commit_intent performs actual M3 claim -> public lifecycle v2 Argus
  append -> public flush. Private registration occurs only after all succeeded in
  the same uncancelled host/deadline scope. The private claim retains that original
  operation deadline; a later Stage/Arm/Release request cannot extend it. A failure burns the consumed intent and
  permanently closes new launches in that owner; no journal/sink repair is implicit.
- StageSupervisor observes current exact C1 frozen membership and matching original
  native READY; no caller membership list or acknowledged flag is trusted. The owner
  derives scope from prepared/unit/descriptor/host/supervisor/AFFA/artifact identities.
- ReleaseOwner.release requires its own registered claim, fresh permit/journal,
  matching original supervisor/C1/gate and current deadline. Arm hashes come from
  actual observations. An observed native unfreeze is a component Release result,
  not readiness, M3 successful outcome or full lifecycle completion.
- Cancel must not wait for a mutation lock held by persistence. No code path kills,
  deletes, discovers/adopts resources, extends original teardown or reconstructs C1.

Required evidence: a real compiler/preparation -> real durable M3 -> real Argus
append+flush -> actual frozen native Stage -> credential-checked RG06 Arm/Release
chain, with a fixed owned child silent before Release. Read accepted Argus records
and independently validate lifecycle payload v2/public redaction. Exercise M3/append/
flush failure, cancellation/late flush, expiry, missing/forged/copied/forked claims,
changed writer/journal/scope, empty/mismatched boundary, native error/replay, and
original C1 cleanup after denial. Preserve old generation-zero admission and full
platform/installed-wheel regression. Keep first candidates and findings before repair.

No complete bounded I/O/bootstrap, operator authentication, ordinary handle, full
M1/kernel-stall/owner-loss, U5–U8 or nine-case runtime closure is inferred.
