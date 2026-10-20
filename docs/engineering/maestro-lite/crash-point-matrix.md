# Broker crash-point matrix

Status: **mapping of the unit-specification crash points onto owned controls; the two gaps
identified on 2026-10-20 and the remaining before-Release-send item are exercised by
`tests/thesis_lite/maestro/test_composed_post_release_loss.py` (SHA
eacef17a2b733e4bf75f05ea9ba687c2859bcf615203fbd361bb32473769ccdd), bounded evidence
`evidence/affa17/crash-matrix-20261020b/` (source 17 passed, installed wheel 17 passed, receipt
f260e97d8234c8bec765c9e0b0d017aed57840dd6a60e29bf41b4e775d831ed7; crash-matrix-20261020a retained
as the predecessor); not a completed M1 crash matrix.** 2026-10-20.

The 024 unit specification requires the broker unit specification to cover every crash
point: prior to containment creation; after retaining containment identity; during spawn;
after child issuance; before/after issuance persistence; before/after supervisor
acknowledgement; before Release; after Release but before M3 outcome; during termination.
Expected observations come from the manually authored tables, not from implementation
state copied into tests. This page records which owned controls exercise each point today.

| Crash point | Existing controls (module::test[params]) | Fault kinds exercised | Status |
| --- | --- | --- | --- |
| prior to containment creation | test_bootstrap_launcher::test_rejection_before_creation_preserves_latch_and_original_parent[10 faults]; test_runtime_startup_failures::test_constructor_conflicts_reject_before_process_or_C1[8 faults] | invalid images/bytes/approval/run/generation/lease/cancelled; constructor conflicts | covered (rejection, zero creation) |
| after retaining containment identity | test_bootstrap_launch_unknown::test_failed_original_identity_is_retained_without_adoption_or_recreation[lost-popen-return, pidfd-open, pidfd-capability]; test_runtime_unknown_birth[birth-exception, pidfd-open-loss] | lost birth identity | covered (unknown birth retained, no adoption) |
| during spawn | test_composed_authority_interruptions::test_atomic_release_cancel_stage[stage-before-send, stage-ack-pending]; test_pre_handle_crash_survival[(stage-before-send, authority), (stage-ack-pending, authority)]; test_composed_post_release_loss::test_spawn_time_storage_loss[stage-before-send, stage-ack-pending] | cancel; authority helper SIGKILL; storage worker SIGKILL | covered (no workload instruction; cleanup-only closure) |
| after child issuance | test_pre_handle_crash_survival[(stage-ack-pending, authority)]; test_composed_issuer_loss::test_original_queued_request_is_dead_before_exact_fallback_release[stage, release] | authority loss after STAGED; registry loss | covered |
| before / after issuance persistence | test_pre_handle_crash_survival[(issuance-before-record, storage), (issuance-after-record, storage)] | storage worker SIGKILL | covered |
| before / after supervisor acknowledgement | test_atomic_release_cancel_stage[stage-ack-pending]; test_runtime_issuer_loss[before-handle] | cancel; issuer loss | covered |
| before Release | test_atomic_release_cancel_stage[release-before-send]; test_composed_issuer_loss[release]; test_composed_post_release_loss::test_release_before_send_loss[authority, storage] | cancel; registry loss; authority/storage SIGKILL exactly before the Release send | covered (finding 372): authority loss releases nothing; storage loss after the durable intent and both revalidations releases exactly once with the outcome absent, never fabricated (design row CP-11) |
| after Release but before M3 outcome | test_atomic_release_cancel_stage[release-ack-pending, release-after-reply]; test_runtime_issuer_loss[after-release]; test_composed_post_release_loss::test_post_release_loss_before_outcome[(release-ack-pending, authority/storage), (release-after-reply, authority/storage)] | cancel; issuer loss; authority/storage SIGKILL | covered: released workload ran exactly once, no started event or outcome recorded after the loss, closure reports workload wait unknown rather than fabricated cleanup, sentinel untouched |
| during termination | test_composed_persistence_termination::test_original_termination_with_live_leader_descendant[stop-before-send, stop-ack-pending, stop-after-reply]; test_terminal_storage_root_loss[storage-stall, storage-death, source-root-loss, evidence-root-loss]; test_terminal_helper_closure[closed, lost-close-ack, required-missing] | authority/storage SIGKILL at STOP windows; storage stall/death; root loss; lost close ACK | covered |

## Gaps implemented on 2026-10-20 (hand-authored expectations in `EXPECTED`, finding 366)

1. Post-Release loss before the M3 outcome: kill the authority helper and, separately, the
   storage worker at `release-ack-pending` and `release-after-reply`; expected: the
   workload that was released keeps its single `EXEC` marker, no second release, cleanup-only
   authority terminates it, closure reports the fenced authority and reaped root, and the
   M3 outcome for that unit is either recorded exactly once or explicitly absent, never
   fabricated. Independent expectations to be authored in a table before the test.
2. Spawn-time storage loss: storage worker killed while the authority is between STAGE send
   and STAGED; expected: no workload instruction, unresolved or cleanup-only ownership,
   sentinel untouched.

Both increments reuse the `execute`/instrumentation pattern of the composed modules and the
unrelated sentinel. Remaining before a complete matrix: an authority/storage loss injected
exactly before the Release send, the independent frozen review of the helper bytes
(IR-ML3-04), and the admitted bounded runtime lane; expected observations for those remain
to be authored in the manually reviewed tables.

## Before-Release-send item implemented (2026-10-20, finding 372)

`test_release_before_send_loss[authority|storage]` injects the loss inside the RELEASE exchange
wrapper, after the durable intent, both storage revalidations and the ARM. The first-authored
table expected no marker for both faults; the authority fault matched, the storage fault released
exactly once (one EXEC marker, 0 started events, 0 outcome records, closure
ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN, late Stage rejected, sentinel untouched). The storage
expectation was corrected after observation and declared so: no storage-liveness check sits
between the last revalidation and the send, none could close that window, and the durable intent
is the authorization, so the case is design row CP-11 from the storage's standpoint. Remaining
before a complete matrix: the independent frozen review of the helper bytes (IR-ML3-04) and the
admitted bounded runtime lane.
